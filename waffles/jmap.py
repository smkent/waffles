import functools
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jmapc
from jmapc import (
    Address,
    Comparator,
    Email,
    EmailQueryFilterCondition,
    EmailSubmission,
    Envelope,
    Identity,
    Mailbox,
    MailboxQueryFilterCondition,
    ResultReference,
)
from jmapc.methods import (
    EmailGet,
    EmailGetResponse,
    EmailQuery,
    EmailSet,
    EmailSubmissionSet,
    EmailSubmissionSetResponse,
    IdentityGet,
    IdentityGetResponse,
    MailboxGet,
    MailboxGetResponse,
    MailboxQuery,
    Method,
    ThreadGet,
    ThreadGetResponse,
)


class JMAPClientWrapper(jmapc.Client):
    def __init__(
        self,
        *args: Any,
        drafts_name: str = "Drafts",
        sent_name: str = "Sent",
        inbox_name: str = "Inbox",
        live_mode: bool = False,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.drafts_name = drafts_name
        self.sent_name = sent_name
        self.inbox_name = inbox_name
        self.live_mode = live_mode

    def _mailbox_query(
        self, query_filter: MailboxQueryFilterCondition
    ) -> Optional[List[Mailbox]]:
        methods: List[Method] = [
            MailboxQuery(filter=query_filter),
            MailboxGet(
                ids=ResultReference(
                    name=MailboxQuery.name,
                    path="/ids",
                    result_of="0",
                ),
            ),
        ]
        results = self.method_calls(methods)
        assert (
            len(results) == 2 and results[1][0] == "1"
        ), "Expected 2 method responses in result"
        assert isinstance(
            results[1][1], MailboxGetResponse
        ), "Expected MailboxGetResponse in response"
        return results[1][1].data

    @functools.lru_cache(maxsize=None)
    def mailbox_by_name(self, name: str) -> Optional[Mailbox]:
        # Retrieve the Mailbox ID for Drafts
        mailboxes = self._mailbox_query(MailboxQueryFilterCondition(name=name))
        if not mailboxes:
            return None
        assert (
            len(mailboxes) == 1
        ), f'Multiple mailboxes found matching "{name}"'
        return mailboxes[0]

    @functools.cached_property
    def identities(self) -> List[Identity]:
        result = self.method_call(IdentityGet())
        assert isinstance(result, IdentityGetResponse)
        return result.data

    @functools.cached_property
    def identities_by_email(self) -> Dict[str, Identity]:
        return {identity.email: identity for identity in self.identities}

    @functools.lru_cache(maxsize=None)
    def identity_by_email(self, email: str) -> Optional[Identity]:
        for identity in self.identities:
            if identity.email == email:
                return identity
        return None

    def get_identity_matching_recipients(
        self, email: Email
    ) -> Optional[Identity]:
        assert email.to
        for recipient in email.to:
            assert recipient.email
            identity = self.identities_by_email.get(recipient.email)
            if identity:
                return identity
        return None

    def get_recent_emails_without_replies(
        self, mailbox_name: str, since: Optional[timedelta] = None
    ) -> List[Email]:
        if not since:
            since = timedelta(days=365)
        mailbox = self.mailbox_by_name(mailbox_name)
        if not mailbox:
            raise Exception(f'No mailbox named "{mailbox_name}" found')
        methods: List[Method] = [
            EmailQuery(
                collapse_threads=True,
                filter=EmailQueryFilterCondition(
                    in_mailbox=mailbox.id,
                    after=datetime.now(tz=timezone.utc) - since,
                ),
                sort=[Comparator(property="receivedAt", is_ascending=False)],
                limit=5,
            ),
            EmailGet(
                ids=ResultReference(
                    name=EmailQuery.name,
                    path="/ids",
                    result_of="0",
                ),
                properties=["threadId"],
            ),
            ThreadGet(
                ids=ResultReference(
                    name=EmailGet.name,
                    path="/list/*/threadId",
                    result_of="1",
                )
            ),
        ]
        results = self.method_calls(methods)
        assert isinstance(results[2][1], ThreadGetResponse)
        email_ids = [
            thread.email_ids[0]
            for thread in results[2][1].data
            if len(thread.email_ids) == 1
        ]
        result = self.method_call(
            EmailGet(
                ids=email_ids,
                fetch_all_body_values=True,
                max_body_value_bytes=1024**2,
            )
        )
        assert isinstance(result, EmailGetResponse)
        return result.data

    def archive_email(self, email: Email) -> None:
        if not email.id:
            return
        inbox = self.mailbox_by_name(self.inbox_name)
        assert isinstance(inbox, Mailbox)
        if not email.mailbox_ids:
            return
        if inbox.id in email.mailbox_ids:
            method = EmailSet(
                update={email.id: {f"mailboxIds/{inbox.id}": None}}
            )
            if not self.live_mode:
                print("<<<<<<<<<<")
                print(json.dumps(method.to_dict(), indent=4, sort_keys=True))
                print(">>>>>>>>>>")
                return
            self.method_call(method)

    def send_email(
        self, email: Email, keep_sent_copy: bool = True
    ) -> Optional[EmailSubmission]:
        drafts_mailbox = self.mailbox_by_name(self.drafts_name)
        assert isinstance(drafts_mailbox, Mailbox)
        if not email.keywords:
            email.keywords = dict()
        email.keywords["$draft"] = True
        if not email.mailbox_ids:
            email.mailbox_ids = dict()
        email.mailbox_ids[drafts_mailbox.id] = True
        assert email.mail_from and email.mail_from[0]
        identity = self.identity_by_email(email.mail_from[0].email)
        assert identity
        assert email.to
        envelope = Envelope(
            mail_from=Address(email.mail_from[0].email),
            rcpt_to=[Address(email=to.email) for to in email.to],
        )

        methods: List[Method] = [
            # Create a draft email in the Drafts mailbox
            EmailSet(create=dict(draft=email)),
        ]
        email_submission_method = EmailSubmissionSet(
            create=dict(
                emailToSend=EmailSubmission(
                    email_id="#draft",
                    identity_id=identity.id,
                    envelope=envelope,
                )
            ),
        )
        if keep_sent_copy:
            sent_mailbox = self.mailbox_by_name(self.sent_name)
            assert isinstance(sent_mailbox, Mailbox)
            # Move from Drafts to Sent on send success
            email_submission_method.on_success_update_email = {
                "#emailToSend": {
                    "keywords/$draft": None,
                    f"mailboxIds/{drafts_mailbox.id}": None,
                    f"mailboxIds/{sent_mailbox.id}": True,
                }
            }
        else:
            # Delete from the Drafts mailbox on send success
            email_submission_method.on_success_destroy_email = ["#emailToSend"]
        methods.append(email_submission_method)
        if not self.live_mode:
            print("<<<<<<<<<<")
            for method in methods:
                print(json.dumps(method.to_dict(), indent=4, sort_keys=True))
            print(">>>>>>>>>>")
            return None
        results = self.method_calls(methods)

        # Retrieve EmailSubmission/set method response from method responses
        email_send_result = results[1][1]
        assert isinstance(
            email_send_result, EmailSubmissionSetResponse
        ), f"Error sending email: f{email_send_result}"

        # Retrieve sent email metadata from EmailSubmission/set method response
        assert email_send_result.created
        assert email_send_result.created["emailToSend"]
        sent_data = email_send_result.created["emailToSend"]

        # Print sent email timestamp
        print(f"Email sent at {sent_data.send_at}")
        return sent_data
