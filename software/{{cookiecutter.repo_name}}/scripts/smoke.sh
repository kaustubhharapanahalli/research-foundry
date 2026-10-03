#!/bin/sh
# Serve the production image as it is deployed, then call /health/ from
# inside the container. `make smoke` mounts this file; it is not in the
# image.
set -eu
python manage.py migrate --noinput
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --daemon \
    --pid /tmp/gunicorn.pid
python - <<'PY'
import json
import sys
import time
import urllib.request

URL = "http://localhost:8000/health/"
for _ in range(60):
    try:
        with urllib.request.urlopen(URL, timeout=2) as response:
            body = json.load(response)
    except OSError:
        time.sleep(0.5)
        continue
    print(f"{URL} -> {body}")
    sys.exit(0 if body == {"status": "ok"} else 1)
sys.exit(f"{URL} did not answer within 30 s")
PY
