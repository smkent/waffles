from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from unittest import mock

from jmapc import (
    Address,
    Comparator,
    Email,
    EmailAddress,
    EmailBodyPart,
    EmailBodyValue,
    EmailHeader,
    EmailQueryFilterCondition,
    EmailSubmission,
    Envelope,
    Identity,
    Mailbox,
    MailboxQueryFilterCondition,
    ResultReference,
    Thread,
)
from jmapc import version as jmapc_version
from jmapc.methods import (
    EmailGet,
    EmailGetResponse,
    EmailQuery,
    EmailSet,
    EmailSetResponse,
    EmailSubmissionSet,
    EmailSubmissionSetResponse,
    IdentityGetResponse,
    MailboxGet,
    MailboxGetResponse,
    MailboxQuery,
    ThreadGet,
    ThreadGetResponse,
)
from replyowl import version as replyowl_version

local_tz_abbrev = datetime(1994, 8, 24, 12, 1, 2).astimezone().strftime("%Z")


def make_identity_get_response() -> IdentityGetResponse:
    return IdentityGetResponse(
        account_id="u1138",
        state="2187",
        not_found=[],
        data=[
            Identity(
                id="ID1",
                name="ness",
                email="ness@onett.example.com",
                reply_to="ness-reply@onett.example.com",
                bcc=None,
                text_signature=None,
                html_signature=None,
                may_delete=False,
            ),
        ],
    )


def make_mailbox_get_call(name: str) -> mock._Call:
    return mock.call(
        [
            MailboxQuery(
                filter=MailboxQueryFilterCondition(
                    name=name, role=None, parent_id=None
                )
            ),
            MailboxGet(
                ids=ResultReference(
                    name=MailboxQuery.name,
                    path="/ids",
                    result_of="0",
                ),
            ),
        ],
    )


def make_mailbox_get_response(
    id: str, name: str
) -> List[Tuple[str, Optional[MailboxGetResponse]]]:
    return [
        ("0", None),
        (
            "1",
            MailboxGetResponse(
                account_id="u1138",
                state="2187",
                not_found=[],
                data=[
                    Mailbox(
                        id=id,
                        sort_order=50,
                        total_emails=100,
                        unread_emails=50,
                        total_threads=40,
                        unread_threads=3,
                        is_subscribed=True,
                        name=name,
                    )
                ],
            ),
        ),
    ]


def make_thread_search_call() -> mock._Call:
    return mock.call(
        [
            EmailQuery(
                collapse_threads=True,
                filter=EmailQueryFilterCondition(
                    in_mailbox="MBX50",
                    after=datetime(1994, 8, 17, 12, 1, 2, tzinfo=timezone.utc),
                ),
                sort=[Comparator(property="receivedAt", is_ascending=False)],
                limit=10,
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
        ],
    )


def make_thread_search_response() -> List[
    Tuple[str, Optional[ThreadGetResponse]]
]:
    return [
        ("0", None),
        ("1", None),
        (
            "2",
            ThreadGetResponse(
                account_id="u1138",
                state="2187",
                not_found=[],
                data=[
                    Thread(
                        id="Tbeef1",
                        email_ids=[
                            "Mdeadbeef",
                        ],
                    ),
                ],
            ),
        ),
    ]


def make_email_get_call() -> mock._Call:
    return mock.call(
        EmailGet(
            ids=["Mdeadbeef"],
            fetch_all_body_values=True,
            max_body_value_bytes=1024**2,
        )
    )


def make_email_get_response(
    is_read: bool, is_in_inbox: bool
) -> EmailGetResponse:
    mailbox_ids = {"MBX2187": True}
    if is_in_inbox:
        mailbox_ids["MBX1000"] = True
    return EmailGetResponse(
        account_id="u1138",
        state="2187",
        not_found=[],
        data=[
            Email(
                id="Mdeadbeef",
                thread_id="Tbeef1",
                to=[EmailAddress(name="Ness", email="ness@onett.example.com")],
                mail_from=[
                    EmailAddress(
                        name="Paula", email="paula@twoson.example.com"
                    )
                ],
                subject="Day Trip to Happy Happy Village",
                message_id=["first@ness.onett.example.com"],
                received_at=datetime.now().astimezone(timezone.utc),
                mailbox_ids=mailbox_ids,
                keywords={"$seen": True} if is_read else None,
                text_body=[EmailBodyPart(part_id="1", type="text/plain")],
                html_body=[EmailBodyPart(part_id="2", type="text/html")],
                body_values={
                    "1": EmailBodyValue(value="plain_text"),
                    "2": EmailBodyValue(value="<b>html</b> text"),
                },
            ),
        ],
    )


def make_email_send_call() -> mock._Call:
    return mock.call(
        [
            EmailSet(
                create=dict(
                    draft=Email(
                        mail_from=[
                            EmailAddress(email="ness@onett.example.com")
                        ],
                        to=[EmailAddress(email="paula@twoson.example.com")],
                        subject="Re: Day Trip to Happy Happy Village",
                        body_values=dict(
                            text=EmailBodyValue(
                                value=(
                                    "**Hi there**. I'm a _test_ message "
                                    "for unit testing.  \n\n----\n\n"
                                    "On Wed Aug 24 1994 12:01 "
                                    f"{local_tz_abbrev}, Paula "
                                    "<paula@twoson.example.com> wrote:\n\n"
                                    "> plain_text"
                                )
                            ),
                            html=EmailBodyValue(
                                value=(
                                    "<!DOCTYPE html>\n<html><head>"
                                    "<title></title></head><body>"
                                    "<b>Hi there</b>. I'm a <i>test</i> "
                                    "message for unit testing.<br/><div>"
                                    "On Wed Aug 24 1994 12:01 "
                                    f"{local_tz_abbrev}, Paula "
                                    "&lt;paula@twoson.example.com&gt; wrote:"
                                    "<br/></div><blockquote "
                                    'style="margin-left: 0.8ex; '
                                    "padding-left: 2ex; "
                                    "border-left: 2px solid #aaa; "
                                    'border-radius: 8px;" type="cite">'
                                    "<b>html</b> text"
                                    "</blockquote></body></html>"
                                )
                            ),
                        ),
                        text_body=[
                            EmailBodyPart(part_id="text", type="text/plain")
                        ],
                        html_body=[
                            EmailBodyPart(part_id="html", type="text/html")
                        ],
                        in_reply_to=["first@ness.onett.example.com"],
                        references=["first@ness.onett.example.com"],
                        headers=[
                            EmailHeader(
                                name="User-Agent",
                                value=(
                                    "wafflesbot/0.0.0 "
                                    f"(jmapc {jmapc_version}, "
                                    f"replyowl {replyowl_version})"
                                ),
                            )
                        ],
                        message_id=[
                            (
                                "1994.08.24T12.01.02"
                                "@wafflesbot.ness.onett.example.com"
                            )
                        ],
                        keywords={"$draft": True},
                        mailbox_ids={"MBX1002": True},
                    )
                )
            ),
            EmailSubmissionSet(
                create=dict(
                    emailToSend=EmailSubmission(
                        email_id="#draft",
                        identity_id="ID1",
                        envelope=Envelope(
                            mail_from=Address(
                                email="ness@onett.example.com",
                                parameters=None,
                            ),
                            rcpt_to=[
                                Address(
                                    email="paula@twoson.example.com",
                                    parameters=None,
                                )
                            ],
                        ),
                    )
                ),
                on_success_update_email={
                    "#emailToSend": {
                        "keywords/$draft": None,
                        "keywords/$seen": True,
                        "mailboxIds/MBX1002": None,
                        "mailboxIds/MBX1003": True,
                    }
                },
            ),
        ]
    )


def make_email_send_response() -> List[
    Tuple[str, Optional[EmailSubmissionSetResponse]]
]:
    return [
        ("0", None),
        (
            "1",
            EmailSubmissionSetResponse(
                account_id="u1138",
                old_state="3000",
                new_state="3001",
                created={
                    "emailToSend": EmailSubmission(
                        send_at=datetime.now().astimezone(timezone.utc)
                    )
                },
                updated=None,
                destroyed=None,
                not_created=None,
                not_updated=None,
                not_destroyed=None,
            ),
        ),
    ]


def make_email_archive_call(
    is_read: bool, is_in_inbox: bool
) -> Optional[mock._Call]:
    updates: Dict[str, Optional[bool]] = {}
    if not is_read:
        updates["keywords/$seen"] = True
    if is_in_inbox:
        updates["mailboxIds/MBX1000"] = None
    if not updates:
        return None
    return mock.call(EmailSet(update={"Mdeadbeef": updates}))


def make_email_archive_response(
    is_read: bool, is_in_inbox: bool
) -> Optional[EmailSetResponse]:
    if is_read and not is_in_inbox:
        return None
    return EmailSetResponse(
        account_id="u1138",
        old_state="3000",
        new_state="3001",
        created=None,
        updated={"Mdeadbeef": None},
        destroyed=None,
        not_created=None,
        not_updated=None,
        not_destroyed=None,
    )
