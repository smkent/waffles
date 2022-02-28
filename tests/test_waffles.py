from datetime import datetime, timezone
from typing import Iterable
from unittest import mock

import pytest
from freezegun import freeze_time
from jmapc import (
    Comparator,
    EmailQueryFilterCondition,
    Mailbox,
    MailboxQueryFilterCondition,
    ResultReference,
)
from jmapc.methods import (
    EmailGet,
    EmailGetResponse,
    EmailQuery,
    MailboxGet,
    MailboxGetResponse,
    MailboxQuery,
    ThreadGet,
    ThreadGetResponse,
)

from waffles import Waffles


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


# @pytest.mark.parametrize("debug", [True, False])
# def test_debug(waffles: Waffles, debug: bool) -> None:
#     log.level == (logging.DEBUG if debug else logging.INFO)


def test_waffles(waffles: Waffles, mock_methods: mock.MagicMock) -> None:
    print(mock_methods)
    mock_responses = [
        [
            ("0", None),
            (
                "1",
                MailboxGetResponse(
                    account_id="u1138",
                    state="2187",
                    not_found=[],
                    data=[
                        Mailbox(
                            id="MBX50",
                            sort_order=50,
                            total_emails=100,
                            unread_emails=50,
                            total_threads=40,
                            unread_threads=3,
                            is_subscribed=True,
                            name="pigeonhole",
                        )
                    ],
                ),
            ),
        ],
        [
            ("0", None),
            ("1", None),
            (
                "2",
                ThreadGetResponse(
                    account_id="u1138",
                    state="2187",
                    not_found=[],
                    data=[],
                ),
            ),
        ],
        EmailGetResponse(
            account_id="u1138",
            state="2187",
            not_found=[],
            data=[],
        ),
    ]

    expected_calls = [
        mock.call(
            [
                MailboxQuery(
                    filter=MailboxQueryFilterCondition(
                        name="pigeonhole", role=None, parent_id=None
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
        ),
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
        ),
        mock.call(
            EmailGet(
                ids=[],
                fetch_all_body_values=True,
                max_body_value_bytes=1024**2,
            )
        ),
    ]
    mock_methods.side_effect = mock_responses
    waffles.process_mailbox("pigeonhole", limit=1)
    assert mock_methods.call_args_list == expected_calls
