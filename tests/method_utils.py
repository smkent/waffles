# import logging
from unittest import mock

from jmapc import Mailbox, MailboxQueryFilterCondition, ResultReference
from jmapc.methods import MailboxGet, MailboxGetResponse, MailboxQuery


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


def make_mailbox_get_response(id: str, name: str) -> MailboxGetResponse:
    return MailboxGetResponse(
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
    )
