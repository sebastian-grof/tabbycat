#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
exec python tabbycat/manage.py runworker notifications adjallocation venues
