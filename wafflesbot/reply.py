from typing import Optional, Tuple

from jmapc import Email
from jmapc import version as jmapc_version
from replyowl import ReplyOwl
from replyowl import version as replyowl_version

from . import version


def _get_email_body_text(email: Email) -> Optional[str]:
    if not email.text_body or not email.body_values:
        return None
    text_data = email.text_body[0]
    if not text_data or not text_data.part_id:
        return None
    return email.body_values[text_data.part_id].value


def _get_email_body_html(email: Email) -> Optional[str]:
    if not email.html_body or not email.body_values:
        return None
    html_data = email.html_body[0]
    if not html_data or not html_data.part_id:
        return None
    return email.body_values[html_data.part_id].value


def compose_reply(
    email: Email, reply_content: str
) -> Tuple[str, Optional[str], Optional[str]]:
    replyowl = ReplyOwl()
    text_body, html_body = replyowl.compose_reply(
        content=reply_content,
        quote_html=_get_email_body_html(email),
        quote_text=_get_email_body_text(email),
        quote_attribution=_quote_attribution_line(email),
    )
    assert text_body
    user_agent = (
        f"wafflesbot/{version} ("
        + ", ".join(
            (
                f"jmapc {jmapc_version}",
                f"replyowl {replyowl_version}",
            )
        )
        + ")"
    )

    return text_body, html_body, user_agent


def _quote_attribution_line(email: Email) -> str:
    assert email.mail_from and email.mail_from[0]
    mail_from = email.mail_from[0]
    assert email.received_at
    sender = f"{mail_from.name or ''} <{mail_from.email}>".strip()
    timestamp = email.received_at.astimezone().strftime(
        "%a %b %-d %Y %H:%M %Z"
    )
    return f"On {timestamp}, {sender} wrote:"
