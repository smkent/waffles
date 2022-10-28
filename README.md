# wafflesbot: Email auto reply bot for [JMAP][jmap] mailboxes

[![PyPI](https://img.shields.io/pypi/v/wafflesbot)][pypi]
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wafflesbot)][pypi]
[![Build](https://img.shields.io/github/checks-status/smkent/waffles/main?label=build)][gh-actions]
[![codecov](https://codecov.io/gh/smkent/waffles/branch/main/graph/badge.svg)][codecov]
[![GitHub stars](https://img.shields.io/github/stars/smkent/waffles?style=social)][repo]

[![wafflesbot][logo]](#)

wafflesbot sends form replies to unreplied emails in a [JMAP][jmap] mailbox
(such as [Fastmail][fastmail]).

wafflesbot excels at automatically asking tech recruiters for compensation
information.

Built on:
* JMAP client: [jmapc][jmapc]
* Quoted email reply assembly: [replyowl][replyowl]

## Installation and usage with Docker

A Docker container is provided which runs wafflesbot to reply to emails via
[JMAP server events][jmap-event-source]. JMAP API authentication and reply
details should be configured using environment variables.

Example `docker-compose.yaml`:

```yaml
version: "3.7"

secrets:
  jmap_api_token:
    file: path/to/file/with/your/jmap_api_token

services:
  waffles:
    image: ghcr.io/smkent/waffles:latest
    environment:
      JMAP_HOST: jmap.example.com
      JMAP_API_TOKEN: /run/secrets/jmap_api_token
      WAFFLES_MAILBOX: folder-or-label-name
      WAFFLES_REPLY_FILE: /autoreply.html
      # WAFFLES_DRY_RUN: "true" # Uncomment to log actions but not send email
      # WAFFLES_DEBUG: "true"   # Uncomment to increase log verbosity
      # Set TZ to your time zone. Often same as the contents of /etc/timezone.
      TZ: PST8PDT
    restart: unless-stopped
    volumes:
      - path/to/your/reply/content.html:/autoreply.html:ro
    secrets:
      - jmap_api_token
```

Start the container by running:

```console
docker-compose up -d
```

Debugging information can be viewed in the container log:

```console
docker-compose logs -f
```

## Installation from PyPI

[wafflesbot is available on PyPI][pypi]:

```console
pip install wafflesbot
```

## Usage

wafflesbot provides the `waffles` command, which can either:
1. Run as a service and reply to emails received via [JMAP server
   events][jmap-event-source] (the default)
2. Run as a script to examine recent emails (such as interactively or via a
   cronjob)

Environment variables:
* `JMAP_HOST`: JMAP server hostname
* `JMAP_API_TOKEN`: JMAP account API token

Required arguments:
* `-m/--mailbox`: Name of the folder to process
* `-r/--reply-content`: Path to file with an HTML reply message

Optional arguments:
* `-d/--debug`: Enable debug logging
* `-l/--limit`: Maximum number of emails replies to send (only valid with
  `-s/--script`)
* `-n/--days`: Only process email received this many days ago or newer (only
  valid with `-s/--script`)
* `-p/--pretend`: Print messages to standard output instead of sending email
* `-s/--script`: Set to run as a script instead of an event-driven service

### Invocation examples

Listen for new emails, and reply to unreplied messages that appear in the
"Recruiters" folder with the message in `my-reply.html`:

```py
JMAP_HOST=jmap.example.com \
JMAP_API_TOKEN=ness__pk_fire \
waffles \
    --mailbox "Recruiters" \
    --reply-content my-reply.html
```

Run as a script and reply to unreplied messages in the "Recruiters" folder with
the message in `my-reply.html`:

```py
JMAP_HOST=jmap.example.com \
JMAP_API_TOKEN=ness__pk_fire \
waffles \
    --script \
    --mailbox "Recruiters" \
    --reply-content my-reply.html
```

## Development

### [Poetry][poetry] installation

Via [`pipx`][pipx]:

```console
pip install pipx
pipx install poetry
pipx inject poetry poetry-dynamic-versioning poetry-pre-commit-plugin
```

Via `pip`:

```console
pip install poetry
poetry self add poetry-dynamic-versioning poetry-pre-commit-plugin
```

### Development tasks

* Setup: `poetry install`
* Run static checks: `poetry run poe lint` or
  `poetry run pre-commit run --all-files`
* Run static checks and tests: `poetry run poe test`

---

Created from [smkent/cookie-python][cookie-python] using
[cookiecutter][cookiecutter]

[codecov]: https://codecov.io/gh/smkent/waffles
[cookie-python]: https://github.com/smkent/cookie-python
[cookiecutter]: https://github.com/cookiecutter/cookiecutter
[fastmail]: https://fastmail.com
[gh-actions]: https://github.com/smkent/waffles/actions?query=branch%3Amain
[jmap]: https://jmap.io
[jmap-event-source]: https://jmap.io/spec-core.html#event-source
[jmapc]: https://github.com/smkent/jmapc
[logo]: https://raw.github.com/smkent/waffles/main/img/waffles.png
[pipx]: https://pypa.github.io/pipx/
[poetry]: https://python-poetry.org/docs/#installation
[pypi]: https://pypi.org/project/wafflesbot/
[replyowl]: https://github.com/smkent/replyowl
[repo]: https://github.com/smkent/waffles
