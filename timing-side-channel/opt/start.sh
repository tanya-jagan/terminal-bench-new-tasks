#!/bin/bash
if [ -z "$SECRET_PASSWORD" ]; then
    echo "ERROR: SECRET_PASSWORD not set" >&2
    exit 1
fi

SECRET_PASSWORD="$SECRET_PASSWORD" python3 /opt/login.py &
sleep 0.5

wait