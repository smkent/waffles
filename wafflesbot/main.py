#!/usr/bin/env python3

import argparse
import os

from .waffles import Waffles


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-r",
        "--reply-content",
        dest="reply_content",
        metavar="file",
        required=True,
        type=argparse.FileType("r"),
        help="File with email reply HTML content",
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
        help="Print messages to standard output instead of sending email",
    )
    ap.add_argument(
        "-s",
        "--script",
        "--no-events",
        dest="events",
        action="store_false",
        help="Run as a script instead of an event-driven service",
    )
    ap.add_argument(
        "-l",
        "--limit",
        "--max-send",
        dest="limit",
        metavar="count",
        default=0,
        type=int,
        help=(
            "Maximum number of email replies to send (0 for no limit) (only "
            "valid with -s/--script) (default: %(default)s)"
        ),
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
            "Only process email received this many days ago or newer (only "
            "valid with -s/--script) (default: %(default)s)"
        ),
    )

    args = ap.parse_args()
    w = Waffles(
        debug=args.debug,
        host=os.environ["JMAP_HOST"],
        api_token=os.environ["JMAP_API_TOKEN"],
        live_mode=not args.dry_run,
        reply_content=args.reply_content.read(),
        newer_than_days=args.newer_than_days,
        mailbox_name=args.mailbox,
    )
    w.run(limit=args.limit, events=args.events)
