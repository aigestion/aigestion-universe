#!/bin/bash
set -e

case "${LOCUST_MODE}" in
    master)
        echo "Starting Locust Master..."
        exec locust -f /locust/locustfile.py \
            --master \
            --master-bind-host=0.0.0.0 \
            --master-bind-port=5557 \
            --web-host="${LOCUST_WEB_HOST}" \
            --web-port="${LOCUST_WEB_PORT}" \
            --html=/locust/report.html \
            --csv=/locust/report \
            --loglevel=INFO
        ;;
    worker)
        echo "Starting Locust Worker..."
        exec locust -f /locust/locustfile.py \
            --worker \
            --master-host="${LOCUST_MASTER_HOST}" \
            --master-port="${LOCUST_MASTER_PORT}" \
            --loglevel=INFO
        ;;
    standalone)
        echo "Starting Locust Standalone..."
        exec locust -f /locust/locustfile.py \
            --headless \
            --users=50 \
            --spawn-rate=5 \
            --run-time=5m \
            --host=http://localhost:5020 \
            --html=/locust/report.html \
            --csv=/locust/report \
            --loglevel=INFO
        ;;
    *)
        echo "Unknown LOCUST_MODE: ${LOCUST_MODE}"
        echo "Valid modes: master, worker, standalone"
        exit 1
        ;;
esac