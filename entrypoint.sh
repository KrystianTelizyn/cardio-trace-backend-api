#!/usr/bin/env sh
set -eu

echo "Applying migrations..."
uv run python manage.py migrate --noinput

echo "Starting application..."
exec uv run python manage.py runserver 0.0.0.0:8000
