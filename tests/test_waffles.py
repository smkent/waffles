from typing import Any, Iterable, List
from unittest import mock

import pytest
from freezegun import freeze_time
from jmapc.methods import IdentityGet

from wafflesbot import Waffles

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


@pytest.fixture
def wafflesbot() -> Iterable[Waffles]:
    with freeze_time("1994-08-24 12:01:02"):
        yield Waffles(
            host="jmap-example.localhost",
            api_token="ness__pk_fire",
            reply_content=(
                "<b>Hi there</b>. I'm a <i>test</i> message "
                "for unit testing.<br />"
            ),
            newer_than_days=7,
        )


@pytest.fixture
def mock_request(wafflesbot: Waffles) -> Iterable[mock.MagicMock]:
    request_mock = mock.MagicMock()
    session_mock = mock.MagicMock(primary_accounts=dict(mail="u1138"))
    with mock.patch.object(
        wafflesbot.client, "_jmap_session", session_mock
    ), mock.patch.object(wafflesbot.client, "request", request_mock):
        yield request_mock


def assert_or_debug_calls(
    call_args_list: mock._CallList, expected_calls: List[mock._Call]
) -> None:
    try:
        assert call_args_list == expected_calls
    except AssertionError:
        try:
            for actual_call, expected_call in zip(
                [c for c in call_args_list], expected_calls
            ):
                if not isinstance(actual_call.args, list):
                    continue
                for actual_arg, expected_arg in zip(
                    actual_call.args, expected_call.args
                ):
                    assert actual_arg == expected_arg
        except Exception:
            raise
        raise


@pytest.mark.parametrize("dry_run", [True, False], ids=["dry_run", "live"])
@pytest.mark.parametrize(
    "original_email_read", [True, False], ids=["read", "unread"]
)
@pytest.mark.parametrize(
    "original_email_in_inbox", [True, False], ids=["in_inbox", "archived"]
)
def test_wafflesbot(
    wafflesbot: Waffles,
    mock_request: mock.MagicMock,
    dry_run: bool,
    original_email_read: bool,
    original_email_in_inbox: bool,
) -> None:
    wafflesbot.client.live_mode = not dry_run
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
        archive_call = make_email_archive_call(
            is_read=original_email_read,
            is_in_inbox=original_email_in_inbox,
        )
        if archive_call:
            expected_calls.append(archive_call)
    mock_responses: List[Any] = []
    mock_responses.append(make_mailbox_get_response("MBX50", "pigeonhole"))
    mock_responses.append(make_thread_search_response())
    mock_responses.append(
        make_email_get_response(
            is_read=original_email_read, is_in_inbox=original_email_in_inbox
        )
    )
    mock_responses.append(make_identity_get_response())
    mock_responses.append(make_mailbox_get_response("MBX1002", "Drafts"))
    mock_responses.append(make_mailbox_get_response("MBX1003", "Sent"))
    if not dry_run:
        mock_responses.append(make_email_send_response())
    mock_responses.append(make_mailbox_get_response("MBX1000", "Inbox"))
    if not dry_run:
        archive_response = make_email_archive_response(
            is_read=original_email_read, is_in_inbox=original_email_in_inbox
        )
        if archive_response:
            mock_responses.append(archive_response)
    mock_request.side_effect = mock_responses

    wafflesbot.process_mailbox("pigeonhole", limit=1)
    assert_or_debug_calls(mock_request.call_args_list, expected_calls)
    with pytest.raises(StopIteration):
        mock_request()
