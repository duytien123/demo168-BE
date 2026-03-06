#!/bin/bash
set -e

python3 /app/app/scripts/first_deploy.py
python3 -m alembic -c alembic.ini --name common upgrade head
# python3 -m alembic -c alembic.ini --name tenant upgrade head

exec "$@"