#!/bin/sh
# Runs CRUD + endpoint tests. Use instead of shell globs in docker compose run.
set -e
cd "$(dirname "$0")"
exec pytest -c test/pytest.ini "$@"
