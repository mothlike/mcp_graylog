#!/bin/sh
set -eu

if [ -z "${GRAYLOG_ENDPOINT:-}" ]; then
  echo "GRAYLOG_ENDPOINT is required" >&2
  exit 1
fi

if [ -z "${GRAYLOG_TOKEN:-}" ]; then
  if [ -z "${GRAYLOG_USERNAME:-}" ] || [ -z "${GRAYLOG_PASSWORD:-}" ]; then
    echo "GRAYLOG_TOKEN or GRAYLOG_USERNAME/GRAYLOG_PASSWORD is required" >&2
    exit 1
  fi
fi

exec "$@"
