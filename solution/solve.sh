#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_SCRIPT="$PROJECT_DIR/environment/scripts/start_api.sh"
MIGRATION_SCRIPT="$PROJECT_DIR/environment/migrate.py"

python "$PROJECT_DIR/environment/scripts/init_db.py"
bash "$API_SCRIPT" &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true; wait "$API_PID" 2>/dev/null || true' EXIT

for attempt in {1..50}; do
    if curl --fail --silent http://127.0.0.1:8080/health >/dev/null; then
        break
    fi
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "Puzzle Tower API exited before becoming healthy." >&2
        exit 1
    fi
    sleep 0.1
done

curl --fail --silent http://127.0.0.1:8080/health >/dev/null || {
    echo "Puzzle Tower API did not become healthy." >&2
    exit 1
}
python "$MIGRATION_SCRIPT"