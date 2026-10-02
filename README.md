# Puzzle Tower State Migration

A small, end-to-end migration system that moves room state from a legacy SQLite database into a Go HTTP API. It demonstrates safe source reads, validated API contracts, repeatable upserts, durable target state, and a deterministic migration manifest without relying on external services.

## What It Does

- Reads every room from SQLite in ascending `room_id` order, without modifying the source.
- Sends each room to `POST /api/v1/sync`; the API validates and upserts by ID, so reruns do not create duplicates.
- Persists the API's destination state as an atomically replaced JSON file.
- Writes `manifest.json` only after all API requests succeed. Its checksum is SHA-256 over the room IDs concatenated in ascending order, with no separators.
- Runs with Python's standard library and a standard-library-only Go API; the migration needs no internet access.

## Quick Start

Requirements: Python 3.10+ and Go 1.19+.

From the repository root, initialize the sample source database:

```bash
python environment/scripts/init_db.py
```

Start the API in one terminal:

```bash
cd environment/api
go run .
```

Run the migration in a second terminal:

```bash
python environment/migrate.py
```

Inspect the health check, migrated state, and manifest:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/v1/rooms
cat environment/manifest.json
```

The source database is `environment/data/tower.sql`; the API destination is `environment/data/rooms.json`. Reset the source sample with `bash environment/scripts/seed_db.sh`.

## API

`POST /api/v1/sync` accepts one room:

```json
{"room_id": 1, "status": "active", "hint_unlocked": 1}
```

It returns `202 Accepted`. Repeating a request for the same ID updates that room. Invalid or incomplete payloads return `400 Bad Request`. `GET /api/v1/rooms` returns the current destination state in ID order; `GET /health` is the readiness check.

## Verification

Install the Python test dependencies once with `python -m pip install -r environment/requirements.txt`.

```bash
cd environment/api && go test ./...
cd ../..
TOWER_PROJECT_ROOT=environment python -m pytest -q tests/test_outputs.py
```

The end-to-end tests build and launch an isolated API, run the migration, compare every destination row to SQLite, verify the manifest checksum, and rerun the migration to check idempotency.

## Configuration

The migration supports `TOWER_DB_PATH`, `TOWER_API_URL`, and `TOWER_MANIFEST_PATH`. The API supports `TOWER_API_ADDR` and `TOWER_STATE_PATH`. Defaults are relative to the project and bind the API to loopback.

## Scope

This is a local migration demonstration, not a multi-node service: API state is stored in one JSON file and concurrent writers across separate processes are not coordinated. The API intentionally binds to loopback and does not implement authentication or TLS.