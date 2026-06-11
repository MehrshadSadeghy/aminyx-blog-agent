#!/bin/sh
set -e
cd "$(dirname "$0")/.."
exec pytest -c test/pytest.ini "$@"
