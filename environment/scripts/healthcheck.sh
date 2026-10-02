#!/bin/bash
# Pings the local API to ensure it is ready to receive migration payloads.

STATUS_CODE=$(curl -o /dev/null -s -w "%{http_code}\n" http://127.0.0.1:8080/health)

if [ "$STATUS_CODE" -eq 200 ]; then
    echo "API is healthy and ready."
    exit 0
else
    echo "API is unreachable. Expected 200, got $STATUS_CODE."
    exit 1
fi