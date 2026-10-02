#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
export TOWER_STATE_PATH="${TOWER_STATE_PATH:-$PROJECT_DIR/data/rooms.json}"

cd "$PROJECT_DIR/api"
exec go run .