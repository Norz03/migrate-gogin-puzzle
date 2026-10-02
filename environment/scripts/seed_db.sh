#!/bin/bash
# Optional script to reset the SQLite database to a clean state.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/init_db.py" --reset
echo "Puzzle Tower source database reset."