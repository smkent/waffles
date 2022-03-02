# import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
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
                    after=datetime(1993, 8, 24, 12, 1, 2, tzinfo=timezone.utc),
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


def make_email_get_response() -> EmailGetResponse:
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
                mailbox_ids={"MBX1000": True},
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
                                    "**Hi there**. I'm a _test_ "
                                    "message for unit testing.  \n\n"
                                )
                            ),
                            html=EmailBodyValue(
                                value=(
                                    "<!DOCTYPE html>\n<html><head>"
                                    "<title></title></head><body>"
                                    "<b>Hi there</b>. I'm a "
                                    "<i>test</i> message for "
                                    "unit testing.<br/></body></html>"
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
                                value="waffles/0.0.0-dev0 (jmapc)",
                            )
                        ],
                        message_id=[
                            (
                                "1994.08.24T12.01.02"
                                "@waffles.dev.example"
                                "_ness.onett.example.com"
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


def make_email_archive_call() -> mock._Call:
    return mock.call(
        EmailSet(
            update={
                "Mdeadbeef": {
                    "keywords/$seen": True,
                    "mailboxIds/MBX1000": None,
                }
            }
        )
    )


def make_email_archive_response() -> EmailSetResponse:
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
