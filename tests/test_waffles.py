from typing import Any, Iterable, List
from unittest import mock

import pytest
from freezegun import freeze_time
from jmapc.methods import IdentityGet

from waffles import Waffles

from .method_utils import (
    make_email_archive_call,
    make_email_archive_response,
    make_email_get_call,
    make_email_get_response,
    make_email_send_call,
    make_email_send_response,
    make_identity_get_response,
    make_mailbox_get_call,
    make_mailbox_get_response,
    make_thread_search_call,
    make_thread_search_response,
)

REPLY_TEMPLATE = (
    "<b>Hi there</b>. I'm a <i>test</i> message for unit testing.<br />"
)


@pytest.fixture
def waffles() -> Iterable[Waffles]:
    with freeze_time("1994-08-24 12:01:02"):
        yield Waffles(
            host="jmap-example.localhost",
            user="ness",
            password="pk_fire",
            reply_template=REPLY_TEMPLATE,
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
    expected_calls: List[mock._Call] = []
    expected_calls.append(make_mailbox_get_call("pigeonhole"))
    expected_calls.append(make_thread_search_call())
    expected_calls.append(make_email_get_call())
    expected_calls.append(mock.call(IdentityGet()))
    expected_calls.append(make_mailbox_get_call("Drafts"))
    expected_calls.append(make_mailbox_get_call("Sent"))
    if not dry_run:
        expected_calls.append(make_email_send_call())
    expected_calls.append(make_mailbox_get_call("Inbox"))
    if not dry_run:
        expected_calls.append(make_email_archive_call())
    mock_responses: List[Any] = []
    mock_responses.append(make_mailbox_get_response("MBX50", "pigeonhole"))
    mock_responses.append(make_thread_search_response())
    mock_responses.append(make_email_get_response())
    mock_responses.append(make_identity_get_response())
    mock_responses.append(make_mailbox_get_response("MBX1002", "Drafts"))
    mock_responses.append(make_mailbox_get_response("MBX1003", "Sent"))
    if not dry_run:
        mock_responses.append(make_email_send_response())
    mock_responses.append(make_mailbox_get_response("MBX1000", "Inbox"))
    if not dry_run:
        mock_responses.append(make_email_archive_response())
    mock_methods.side_effect = mock_responses

    waffles.process_mailbox("pigeonhole", limit=1)
    assert mock_methods.call_args_list == expected_calls
