#!/usr/bin/env bash
#   Shorthand to run django worker in docker
set -euo pipefail

cd tabbycat

# Run worker
exec python ./manage.py runworker notifications adjallocation venues feedbackexport
