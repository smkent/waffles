import logging
import re
from datetime import datetime
from typing import Any, Optional

from jmapc import (
    Email,
    EmailAddress,
    EmailBodyPart,
    EmailBodyValue,
    EmailHeader,
    Identity,
)
from jmapc.logging import log
from replyowl import ReplyOwl

from .jmap import JMAPClientWrapper


class Waffles:
    def __init__(
        self,
        *args: Any,
        reply_template: str,
        debug: bool = False,
        **kwargs: Any,
    ):
        self.client = JMAPClientWrapper(*args, **kwargs)
        self.replyowl = ReplyOwl()
        self.reply_template = reply_template
        logging.basicConfig()
        log.setLevel(logging.DEBUG if debug else logging.INFO)

    def process_mailbox(self, mailbox_name: str, limit: int = 0) -> None:
        emails = self.client.get_recent_emails_without_replies(mailbox_name)
        for i, email in enumerate(emails):
            print(
                f"[{email.received_at}] FROM {email.mail_from}: "
                f"{email.subject}"
            )
            self._reply_to_email(email)
            self.client.archive_email(email)
            if i >= limit:
                break

    def _reply_to_email(self, email: Email) -> None:
        identity = self.client.get_identity_matching_recipients(email)
        assert isinstance(
            identity, Identity
        ), "No identity found matching any recipients"
        subject = f"Re: {email.subject}"
        mail_to = self._get_reply_address(email)
        text_body, html_body = self.replyowl.compose_reply(
            content=self.reply_template,
            quote_html=self._get_email_body_html(email),
            quote_text=self._get_email_body_text(email),
            quote_attribution=self._reply_attribution_line(email),
        )
        assert email.message_id and email.message_id[0]
        email = Email(
            mail_from=[EmailAddress(email=identity.email)],
            to=[EmailAddress(email=mail_to)],
            subject=subject,
            body_values=dict(
                text=EmailBodyValue(value=text_body),
                html=EmailBodyValue(value=html_body),
            ),
            text_body=[EmailBodyPart(part_id="text", type="text/plain")],
            html_body=[EmailBodyPart(part_id="html", type="text/html")],
            in_reply_to=email.message_id,
            references=(email.references or []) + email.message_id,
            headers=[
                EmailHeader(
                    name="User-Agent", value="waffles/0.0.0-dev0 (jmapc)"
                )
            ],
            message_id=[self._make_messageid(identity.email)],
        )
        self.client.send_email(email, keep_sent_copy=True)

    def _make_messageid(self, mail_from: str) -> str:
        dt = datetime.utcnow().isoformat().replace(":", ".").replace("-", ".")
        dotaddr = re.sub(r"\W", ".", mail_from)
        return f"{dt}@waffles.dev.example_{dotaddr}"

    def _get_email_body_text(self, email: Email) -> Optional[str]:
        if not email.text_body or not email.body_values:
            return None
        text_data = email.text_body[0]
        if not text_data or not text_data.part_id:
            return None
        return email.body_values[text_data.part_id].value

    def _get_email_body_html(self, email: Email) -> Optional[str]:
        if not email.html_body or not email.body_values:
            return None
        html_data = email.html_body[0]
        if not html_data or not html_data.part_id:
            return None
        return email.body_values[html_data.part_id].value

    def _reply_attribution_line(self, email: Email) -> str:
        assert email.mail_from and email.mail_from[0]
        mail_from = email.mail_from[0]
        assert email.received_at
        sender = f"{mail_from.name or ''} <{mail_from.email}>".strip()
        timestamp = email.received_at.astimezone().strftime(
            "%a %b %-d %Y %H:%M %Z"
        )
        return f"On {timestamp}, {sender} wrote:"

    def _get_reply_address(self, email: Email) -> str:
        if email.reply_to:
            assert email.reply_to[0]
            if email.reply_to[0].email:
                return email.reply_to[0].email
        assert email.mail_from
        assert email.mail_from[0]
        from_email = email.mail_from[0].email
        assert from_email
        return from_email
