#!/usr/bin/env python3

import argparse
import os

from .waffles import Waffles


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-r",
        "--reply-template",
        dest="reply_template",
        metavar="file",
        required=True,
        type=argparse.FileType("r"),
        help="Email reply template",
    )
    ap.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logs",
    )
    ap.add_argument(
        "-m",
        "--mailbox",
        "--folder",
        "--label",
        dest="mailbox",
        metavar="name",
        help="Folder or label to examine",
    )
    ap.add_argument(
        "-p",
        "--pretend",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help=(
            "Instead of sending email, "
            "print email API methods to standard output"
        ),
    )
    ap.add_argument(
        "-l",
        "--limit",
        "--max-send",
        dest="limit",
        metavar="count",
        default=0,
        type=int,
        help="Maximum number of email replies to send (0 for no limit)",
    )
    ap.add_argument(
        "-n",
        "--days",
        "--newer-than-days",
        dest="newer_than_days",
        metavar="days",
        default=1,
        type=int,
        help=(
            "Only process email received this many days ago or newer "
            "(default: %(default)s)"
        ),
    )

    args = ap.parse_args()
    w = Waffles(
        debug=args.debug,
        host=os.environ["JMAP_HOST"],
        user=os.environ["JMAP_USER"],
        password=os.environ["JMAP_PASSWORD"],
        live_mode=not args.dry_run,
        reply_template=args.reply_template.read(),
        newer_than_days=args.newer_than_days,
    )
    w.process_mailbox(args.mailbox, limit=args.limit)
