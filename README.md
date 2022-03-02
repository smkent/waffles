# wafflesbot: Email auto reply bot for [JMAP][jmap] mailboxes

[![PyPI](https://img.shields.io/pypi/v/wafflesbot)][pypi]
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wafflesbot)][pypi]
[![Build](https://img.shields.io/github/checks-status/smkent/wafflesbot/master?label=build)][gh-actions]
[![codecov](https://codecov.io/gh/smkent/wafflesbot/branch/master/graph/badge.svg)][codecov]
[![GitHub stars](https://img.shields.io/github/stars/smkent/wafflesbot?style=social)][repo]

wafflesbot sends form replies to unreplied emails in a [JMAP][jmap] mailbox
(such as [Fastmail][fastmail]).

wafflesbot excels at automatically asking tech recruiters for compensation
information.

Built on:
* JMAP client: [jmapc][jmapc]
* Quoted email reply assembly: [replyowl][replyowl]

## Installation

[wafflesbot is available on PyPI][pypi]:

```
pip install wafflesbot
```

## Usage

wafflesbot provides the `waffles` command which can be run interactively or as a
cronjob.

Environment variables:
* `JMAP_HOST`: JMAP server hostname
* `JMAP_USER`: Email account username
* `JMAP_PASSWORD`: Email account password (likely an app password if 2-factor
  authentication is enabled with your provider)

Required arguments:
* `-m/--mailbox`: Name of the folder to process
* `-r/--reply-template`: Path to file with an HTML reply message

### Invocation examples

Reply to messages in the "Recruiters" folder with the message in `my-reply.html`:
```py
JMAP_HOST=jmap.example.com \
JMAP_USER=ness \
JMAP_PASSWORD=pk_fire \
waffles \
    --mailbox "Recruiters" \
    --reply-template my-reply.html
```

Additional argument examples:

* Only reply to messages received within the last day:
  * `waffles -m "Recruiters" -r my-reply.html --days 1` (or `-n`)
* Send at most 2 emails before exiting:
  * `waffles -m "Recruiters" -r my-reply.html --limit 2` (or `-l`)
* Instead of sending mail, print constructed email replies to standard output:
  * `waffles -m "Recruiters" -r my-reply.html --dry-run` (or `-p`)
* Log JMAP requests and responses to the debug logger:
  * `waffles -m "Recruiters" -r my-reply.html --debug` (or `-d`)

## Development

Prerequisites: [Poetry][poetry]

* Setup: `poetry install`
* Run all tests: `poetry run poe test`
* Fix linting errors: `poetry run poe lint`

---

Created from [smkent/cookie-python][cookie-python] using
[cookiecutter][cookiecutter]

[codecov]: https://codecov.io/gh/smkent/wafflesbot
[cookie-python]: https://github.com/smkent/cookie-python
[cookiecutter]: https://github.com/cookiecutter/cookiecutter
[fastmail]: https://fastmail.com
[gh-actions]: https://github.com/smkent/wafflesbot/actions?query=branch%3Amaster
[jmap]: https://jmap.io
[jmapc]: https://github.com/smkent/jmapc
[poetry]: https://python-poetry.org/docs/#installation
[pypi]: https://pypi.org/project/wafflesbot/
[replyowl]: https://github.com/smkent/replyowl
[repo]: https://github.com/smkent/wafflesbot
