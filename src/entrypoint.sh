#!/bin/sh

python /app/monitor_service.py &
exec gunicorn -b 0.0.0.0:5000 monitor_api:app
