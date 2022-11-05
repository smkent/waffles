import logging
import time
from datetime import timedelta
from typing import Any

from jmapc import Email
from jmapc.logging import log as jmapc_log

from .jmap import JMAPClientWrapper
from .logging import log
from .reply import compose_reply


class Waffles:
    def __init__(
        self,
        *args: Any,
        reply_content: str,
        mailbox_name: str,
        newer_than_days: int = 1,
        debug: bool = False,
        **kwargs: Any,
    ):
        self.client = JMAPClientWrapper.create_with_api_token(
            *args,
            mailbox_name=mailbox_name,
            new_email_callback=self._handle_email,
            **kwargs,
        )
        self.mailbox_name = mailbox_name
        self.reply_content = reply_content
        self.newer_than_days = newer_than_days
        self._setup_logging(debug=debug)
        jmapc_log.setLevel(logging.DEBUG if debug else logging.INFO)

    def run(self, limit: int = 0, events: bool = True) -> None:
        if events:
            self.client.process_events()
        else:
            self.client.process_recent_emails_without_replies(
                since=(
                    timedelta(days=self.newer_than_days)
                    if self.newer_than_days
                    else None
                ),
                limit=limit,
            )

    def _handle_email(self, email: Email) -> None:
        log.info(f"Email from {email.mail_from} -> {email.subject}")
        self._reply(email)
        self.client.archive_email(email)

    def _reply(self, email: Email) -> None:
        text_body, html_body, user_agent = compose_reply(
            email, self.reply_content
        )
        self.client.send_reply_to_email(
            email,
            text_body,
            html_body,
            user_agent=user_agent,
            keep_sent_copy=True,
        )

    def _setup_logging(self, debug: bool) -> None:
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
        log.setLevel(logging.DEBUG if debug else logging.INFO)
