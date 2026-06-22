#!/bin/sh
set -e

mkdir -p "$(dirname "${SQLITE_DB_PATH:-/opt/vue-fastapi-admin/db.sqlite3}")"
mkdir -p "${REDBOOK_UPLOAD_ROOT:-/opt/vue-fastapi-admin/storage/redbook_uploads}"

nginx
exec python run.py
