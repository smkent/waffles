FROM python:3-alpine
RUN apk add --no-cache tini
COPY docker/entrypoint /

COPY . /python-build
RUN python3 -m pip install /python-build && rm -rf /python-build

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/entrypoint"]
