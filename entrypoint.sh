#!/bin/sh
set -e

python -c "import os, socket, time; host=os.environ.get('POSTGRES_HOST', 'db'); port=int(os.environ.get('POSTGRES_PORT', '5432')); deadline=time.time()+60
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        if time.time() >= deadline:
            raise SystemExit('PostgreSQL is not available')
        time.sleep(1)"

python manage.py migrate
python manage.py seed_demo_data
exec python manage.py runserver 0.0.0.0:8000
