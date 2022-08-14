import logging
import time
from datetime import timedelta
from typing import Any, Optional

from jmapc import Email
from jmapc.logging import log

from .jmap import JMAPClientWrapper
from .reply import compose_reply


class Waffles:
    def __init__(
        self,
        *args: Any,
        reply_content: str,
        newer_than_days: int = 1,
        debug: bool = False,
        **kwargs: Any,
    ):
        self.client = JMAPClientWrapper.create_with_api_token(*args, **kwargs)
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
            self._reply(email)
            self.client.archive_email(email)
            if limit and i + 1 >= limit:
                break

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
