from typing import Any
from collections.abc import Iterable
from unittest import mock

import pytest
import sseclient
from freezegun import freeze_time
from jmapc.methods import IdentityGet

from wafflesbot import Waffles

from .method_utils import (
    make_email_archive_call,
    make_email_archive_response,
    make_email_changes_call,
    make_email_changes_response,
    make_email_event,
    make_email_get_call,
    make_email_get_response,
    make_email_send_call,
    make_email_send_response,
    make_identity_get_response,
    make_mailbox_get_call,
    make_mailbox_get_response,
    make_thread_get_call,
    make_thread_get_response,
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
            mailbox_name="pigeonhole",
        )


@pytest.fixture
def mock_request(wafflesbot: Waffles) -> Iterable[mock.MagicMock]:
    request_mock = mock.MagicMock()
    session_mock = mock.MagicMock(
        primary_accounts=dict(mail="u1138"),
        event_source_url="https://jmap-example.localhost/events/",
    )
    with (
        mock.patch("jmapc.client.Client.jmap_session", session_mock),
        mock.patch.object(wafflesbot.client, "request", request_mock),
    ):
        yield request_mock


@pytest.fixture(autouse=True)
def mock_events(wafflesbot: Waffles) -> Iterable[list[sseclient.Event]]:
    mock_events_data: list[sseclient.Event] = []
    with mock.patch.object(wafflesbot.client, "_events", mock_events_data):
        yield mock_events_data


def assert_or_debug_calls(
    call_args_list: mock._CallList, expected_calls: list[mock._Call]
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


@pytest.mark.parametrize(
    "events", [True, False], ids=["events", "script_mode"]
)
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
    mock_events: list[sseclient.Event],
    dry_run: bool,
    events: bool,
    original_email_read: bool,
    original_email_in_inbox: bool,
) -> None:
    wafflesbot.client.live_mode = not dry_run
    mock_events.append(make_email_event(email_state="1118"))
    mock_events.append(make_email_event(email_state="1119"))
    expected_calls: list[mock._Call] = []
    expected_calls.append(make_mailbox_get_call("pigeonhole"))
    if events:
        expected_calls.append(make_email_changes_call(since_state="1118"))
        expected_calls.append(
            make_email_get_call(properties=["threadId", "mailboxIds"])
        )
        expected_calls.append(make_thread_get_call())
        expected_calls.append(make_email_get_call(fetch_all_body_values=True))
    else:
        expected_calls.append(make_thread_search_call())
        expected_calls.append(make_email_get_call(fetch_all_body_values=True))
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
    mock_responses: list[Any] = []
    mock_responses.append(make_mailbox_get_response("MBX50", "pigeonhole"))
    if events:
        mock_responses.append(make_email_changes_response())
        mock_responses.append(
            make_email_get_response(
                is_read=original_email_read,
                is_in_inbox=original_email_in_inbox,
                additional_mailbox="MBX50",
            )
        )
        mock_responses.append(make_thread_get_response())
        mock_responses.append(
            make_email_get_response(
                is_read=original_email_read,
                is_in_inbox=original_email_in_inbox,
            )
        )
    else:
        mock_responses.append(make_thread_search_response())
        mock_responses.append(
            make_email_get_response(
                is_read=original_email_read,
                is_in_inbox=original_email_in_inbox,
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
    wafflesbot.run(events=events)
    assert_or_debug_calls(mock_request.call_args_list, expected_calls)
    with pytest.raises(StopIteration):
        mock_request()


def test_wafflesbot_no_matching_identity(
    wafflesbot: Waffles,
    mock_request: mock.MagicMock,
    mock_events: list[sseclient.Event],
) -> None:
    original_email_read = False
    original_email_in_inbox = True
    wafflesbot.client.live_mode = True
    mock_events.append(make_email_event(email_state="1118"))
    mock_events.append(make_email_event(email_state="1119"))
    expected_calls: list[mock._Call] = []
    expected_calls.append(make_mailbox_get_call("pigeonhole"))
    expected_calls.append(make_email_changes_call(since_state="1118"))
    expected_calls.append(
        make_email_get_call(properties=["threadId", "mailboxIds"])
    )
    expected_calls.append(make_thread_get_call())
    expected_calls.append(make_email_get_call(fetch_all_body_values=True))
    expected_calls.append(mock.call(IdentityGet()))
    mock_responses: list[Any] = []
    mock_responses.append(make_mailbox_get_response("MBX50", "pigeonhole"))
    mock_responses.append(make_email_changes_response())
    mock_responses.append(
        make_email_get_response(
            is_read=original_email_read,
            is_in_inbox=original_email_in_inbox,
            additional_mailbox="MBX50",
        )
    )
    mock_responses.append(make_thread_get_response())
    mock_responses.append(
        make_email_get_response(
            is_read=original_email_read,
            is_in_inbox=original_email_in_inbox,
        )
    )
    mock_responses.append(
        make_identity_get_response(email="unknown.identity@example.com")
    )
    mock_request.side_effect = mock_responses
    wafflesbot.run(events=True)
    assert_or_debug_calls(mock_request.call_args_list, expected_calls)
    with pytest.raises(StopIteration):
        mock_request()


@pytest.mark.parametrize("dry_run", [True, False], ids=["dry_run", "live"])
@pytest.mark.parametrize(
    "in_folder", [True, False], ids=["in_folder", "not_in_folder"]
)
@pytest.mark.parametrize(
    "original_email_read", [True, False], ids=["read", "unread"]
)
@pytest.mark.parametrize(
    "original_email_in_inbox", [True, False], ids=["in_inbox", "archived"]
)
def test_wafflesbot_ignore_event(
    wafflesbot: Waffles,
    mock_request: mock.MagicMock,
    mock_events: list[sseclient.Event],
    original_email_read: bool,
    original_email_in_inbox: bool,
    dry_run: bool,
    in_folder: bool,
) -> None:
    wafflesbot.client.live_mode = not dry_run
    mock_events.append(make_email_event(email_state="1118"))
    mock_events.append(make_email_event(email_state="1119"))
    expected_calls: list[mock._Call] = []
    expected_calls.append(make_mailbox_get_call("pigeonhole"))
    expected_calls.append(make_email_changes_call(since_state="1118"))
    expected_calls.append(
        make_email_get_call(properties=["threadId", "mailboxIds"])
    )
    mock_responses: list[Any] = []
    mock_responses.append(make_mailbox_get_response("MBX50", "pigeonhole"))
    mock_responses.append(make_email_changes_response())
    mock_responses.append(
        make_email_get_response(
            is_read=original_email_read,
            is_in_inbox=original_email_in_inbox,
            additional_mailbox=("MBX50" if in_folder else None),
        )
    )
    if in_folder:
        expected_calls.append(make_thread_get_call())
        mock_responses.append(make_thread_get_response(has_email_id=False))
    mock_request.side_effect = mock_responses
    wafflesbot.run(events=True)
    assert_or_debug_calls(mock_request.call_args_list, expected_calls)
    with pytest.raises(StopIteration):
        mock_request()


@pytest.mark.parametrize("dry_run", [True, False], ids=["dry_run", "live"])
def test_wafflesbot_event_error(
    wafflesbot: Waffles,
    mock_request: mock.MagicMock,
    mock_events: list[sseclient.Event],
    dry_run: bool,
) -> None:
    wafflesbot.client.live_mode = not dry_run
    mock_events.append(make_email_event(email_state="1118"))
    mock_events.append(make_email_event(email_state="1119"))
    expected_calls: list[mock._Call] = []
    expected_calls.append(make_mailbox_get_call("pigeonhole"))
    mock_responses: list[Any] = []
    mock_responses.append(Exception)
    mock_request.side_effect = mock_responses
    wafflesbot.run(events=True)  # Should not raise an exception
    assert_or_debug_calls(mock_request.call_args_list, expected_calls)
    with pytest.raises(StopIteration):
        mock_request()
