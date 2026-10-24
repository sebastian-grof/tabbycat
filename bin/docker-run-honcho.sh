#!/usr/bin/env bash
#   Shorthand to migrate and run honcho in docker
set -euo pipefail

cd tabbycat

# Migrate (can't do it during build; no db connnection)
if [[ "${RUN_MIGRATIONS:-1}" == "1" ]]; then
  python ./manage.py migrate --no-input
fi

# Needed to ensure daphne works properly
rm -f /tmp/asgi.socket /tmp/asgi.socket.lock

# Run honcho
cd ..
exec honcho -f ./ProcfileMulti.docker start
