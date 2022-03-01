from datetime import datetime, timezone
from typing import Any, Iterable, List
from unittest import mock

import pytest
from freezegun import freeze_time
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
    ResultReference,
    Thread,
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
    ThreadGet,
    ThreadGetResponse,
)

from waffles import Waffles

from .method_utils import make_mailbox_get_call, make_mailbox_get_response


@pytest.fixture
def waffles() -> Iterable[Waffles]:
    with freeze_time("1994-08-24 12:01:02"):
        yield Waffles(
            host="jmap-example.localhost",
            user="ness",
            password="pk_fire",
        )


@pytest.fixture
def mock_methods(waffles: Waffles) -> Iterable[mock.MagicMock]:
    methods_mock = mock.MagicMock()
    session_mock = mock.MagicMock(primary_accounts=dict(mail="u1138"))
    with mock.patch.object(
        waffles.client, "_session", session_mock
    ), mock.patch.object(
        waffles.client, "method_call", methods_mock
    ), mock.patch.object(
        waffles.client, "method_calls", methods_mock
    ):
        yield methods_mock


@pytest.mark.parametrize("dry_run", [True, False], ids=["dry_run", "live"])
def test_waffles(
    waffles: Waffles, mock_methods: mock.MagicMock, dry_run: bool
) -> None:
    waffles.client.live_mode = not dry_run
    mock_responses: List[Any] = []
    mock_responses.append(
        [("0", None), ("1", make_mailbox_get_response("MBX50", "pigeonhole"))]
    )
    mock_responses.append(
        [
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
    )
    mock_responses.append(
        EmailGetResponse(
            account_id="u1138",
            state="2187",
            not_found=[],
            data=[
                Email(
                    id="Mdeadbeef",
                    thread_id="Tbeef1",
                    to=[
                        EmailAddress(
                            name="Ness", email="ness@onett.example.com"
                        )
                    ],
                    mail_from=[
                        EmailAddress(
                            name="Paula", email="paula@twoson.example.com"
                        )
                    ],
                    subject="Day Trip to Happy Happy Village",
                    message_id=["first@ness.onett.example.com"],
                    received_at=datetime.now().astimezone(timezone.utc),
                ),
            ],
        )
    )
    mock_responses.append(
        IdentityGetResponse(
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
    )
    mock_responses.append(
        [("0", None), ("1", make_mailbox_get_response("MBX1002", "Drafts"))]
    )
    mock_responses.append(
        [("0", None), ("1", make_mailbox_get_response("MBX1003", "Sent"))]
    )
    if not dry_run:
        mock_responses.append(
            [
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
            ],
        )
    mock_responses.append(
        [("0", None), ("1", make_mailbox_get_response("MBX1000", "Inbox"))]
    )

    expected_calls: List[mock._Call] = []
    expected_calls.append(make_mailbox_get_call("pigeonhole"))
    expected_calls.append(
        mock.call(
            [
                EmailQuery(
                    collapse_threads=True,
                    filter=EmailQueryFilterCondition(
                        in_mailbox="MBX50",
                        after=datetime(
                            1993, 8, 24, 12, 1, 2, tzinfo=timezone.utc
                        ),
                    ),
                    sort=[
                        Comparator(property="receivedAt", is_ascending=False)
                    ],
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
    )
    expected_calls.append(
        mock.call(
            EmailGet(
                ids=["Mdeadbeef"],
                fetch_all_body_values=True,
                max_body_value_bytes=1024**2,
            )
        )
    )
    expected_calls.append(mock.call(IdentityGet()))
    expected_calls.append(make_mailbox_get_call("Drafts"))
    expected_calls.append(make_mailbox_get_call("Sent"))
    if not dry_run:
        expected_calls.append(
            mock.call(
                [
                    EmailSet(
                        create=dict(
                            draft=Email(
                                mail_from=[
                                    EmailAddress(
                                        email="ness@onett.example.com"
                                    )
                                ],
                                to=[
                                    EmailAddress(
                                        email="paula@twoson.example.com"
                                    )
                                ],
                                subject="Re: Day Trip to Happy Happy Village",
                                body_values=dict(
                                    body=EmailBodyValue(
                                        value=(
                                            "Reply to your email below:"
                                            "\n\n----\n\n(no message)"
                                        )
                                    )
                                ),
                                text_body=[
                                    EmailBodyPart(
                                        part_id="body", type="text/plain"
                                    )
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
                                        "1994.08.24T19.01.02"
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
                                "mailboxIds/MBX1002": None,
                                "mailboxIds/MBX1003": True,
                            }
                        },
                    ),
                ]
            )
        )
    expected_calls.append(make_mailbox_get_call("Inbox"))
    mock_methods.side_effect = mock_responses
    waffles.process_mailbox("pigeonhole", limit=1)
    assert mock_methods.call_args_list == expected_calls
