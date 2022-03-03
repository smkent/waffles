import logging
import time
from datetime import timedelta
from typing import Any, Optional

from jmapc import Email
from jmapc import version as jmapc_version
from jmapc.logging import log
from replyowl import ReplyOwl
from replyowl import version as replyowl_version

from . import version
from .jmap import JMAPClientWrapper


class Waffles:
    def __init__(
        self,
        *args: Any,
        reply_content: str,
        newer_than_days: int = 1,
        debug: bool = False,
        **kwargs: Any,
    ):
        self.client = JMAPClientWrapper(*args, **kwargs)
        self.replyowl = ReplyOwl()
        self.reply_content = reply_content
        self.newer_than_days = newer_than_days
        self._setup_logging()
        log.setLevel(logging.DEBUG if debug else logging.INFO)

    def process_mailbox(self, mailbox_name: str, limit: int = 0) -> None:
        since: Optional[timedelta] = None
        if self.newer_than_days:
            since = timedelta(days=self.newer_than_days)
        emails = self.client.get_recent_emails_without_replies(
            mailbox_name, since=since
        )
        for i, email in enumerate(emails):
            print(
                f"[{email.received_at}] FROM {email.mail_from}: "
                f"{email.subject}"
            )
            self._reply_to_email(email)
            self.client.archive_email(email)
            if limit and i + 1 >= limit:
                break

    def _setup_logging(self) -> None:
        class UTCFormatter(logging.Formatter):
            converter = time.gmtime

        logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = UTCFormatter(
            "%(asctime)s %(name)-12s %(levelname)-8s "
            "[%(filename)s:%(funcName)s:%(lineno)d] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        log.setLevel(logging.INFO)

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

    def _reply_to_email(self, email: Email) -> None:
        text_body, html_body = self.replyowl.compose_reply(
            content=self.reply_content,
            quote_html=self._get_email_body_html(email),
            quote_text=self._get_email_body_text(email),
            quote_attribution=self._quote_attribution_line(email),
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

        self.client.send_reply_to_email(
            email,
            text_body,
            html_body,
            user_agent=user_agent,
            keep_sent_copy=True,
        )

    def _quote_attribution_line(self, email: Email) -> str:
        assert email.mail_from and email.mail_from[0]
        mail_from = email.mail_from[0]
        assert email.received_at
        sender = f"{mail_from.name or ''} <{mail_from.email}>".strip()
        timestamp = email.received_at.astimezone().strftime(
            "%a %b %-d %Y %H:%M %Z"
        )
        return f"On {timestamp}, {sender} wrote:"
