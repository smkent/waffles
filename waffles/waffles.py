import logging
import re
from datetime import datetime, timezone
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

from .jmap import JMAPClientWrapper


class Waffles:
    def __init__(self, *args: Any, debug: bool = False, **kwargs: Any):
        self.client = JMAPClientWrapper(*args, **kwargs)
        logging.basicConfig()
        log.setLevel(logging.DEBUG if debug else logging.INFO)

    def process_mailbox(self, mailbox_name: str, limit: int = 0) -> None:
        emails = self.client.get_recent_emails_without_replies(mailbox_name)
        for email in emails:
            print(
                f"[{email.received_at}] FROM {email.mail_from}: "
                f"{email.subject}"
            )
            self.reply_to_email(email)
            self.client.archive_email(email)
            break

    def _msgid(self, mail_from: str) -> str:
        dt = (
            datetime.now()
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
            .isoformat()
            .replace(":", ".")
            .replace("-", ".")
        )
        dotaddr = re.sub(r"\W", ".", mail_from)
        return f"{dt}@waffles.dev.example_{dotaddr}"

    def get_email_body_text(self, email: Email) -> Optional[str]:
        if not email.text_body or not email.body_values:
            return None
        text_data = email.text_body[0]
        if not text_data or not text_data.part_id:
            return None
        return email.body_values[text_data.part_id].value

    def reply_to_email(self, email: Email) -> None:
        identity = self.client.get_identity_matching_recipients(email)
        assert isinstance(
            identity, Identity
        ), "No identity found matching any recipients"
        subject = f"Re: {email.subject}"
        if email.reply_to:
            assert email.reply_to[0]
            mail_to = email.reply_to[0].email
        else:
            assert email.mail_from and email.mail_from[0]
            mail_to = email.mail_from[0].email
        old_body = self.get_email_body_text(email) or "(no message)"
        body = f"Reply to your email below:\n\n----\n\n{old_body}"
        assert email.message_id and email.message_id[0]

        email = Email(
            mail_from=[EmailAddress(email=identity.email)],
            to=[EmailAddress(email=mail_to)],
            subject=subject,
            body_values=dict(body=EmailBodyValue(value=body)),
            text_body=[EmailBodyPart(part_id="body", type="text/plain")],
            in_reply_to=email.message_id,
            references=(email.references or []) + email.message_id,
            headers=[
                EmailHeader(
                    name="User-Agent", value="waffles/0.0.0-dev0 (jmapc)"
                )
            ],
            message_id=[self._msgid(identity.email)],
        )
        self.client.send_email(email, keep_sent_copy=True)
