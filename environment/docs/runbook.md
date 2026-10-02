# Puzzle Tower Migration Runbook

Run the API and migration on the same machine. The API binds to loopback by default; no external service or network access is required.

## Initialize

From the repository root, create the sample SQLite database if it does not exist:

```bash
python environment/scripts/init_db.py
```

To reset all source rooms to `locked` with hints disabled:

```bash
bash environment/scripts/seed_db.sh
```

## Start the API

In a dedicated terminal:

```bash
cd environment/api
go run .
```

Wait for `GET http://127.0.0.1:8080/health` to return `200` before starting the migration.

## Run and Verify

In another terminal, from the repository root:

```bash
python environment/migrate.py
curl http://127.0.0.1:8080/api/v1/rooms
```

The migration writes `environment/manifest.json` only after every room is accepted. Its SHA-256 checksum uses the ascending room IDs concatenated without separators. Running the migration again is safe.

## Troubleshooting

- If the API cannot bind, set `TOWER_API_ADDR` to another loopback port and set `TOWER_API_URL` to the matching URL before running the migration.
- If the source file is missing, rerun the initializer. If it needs a clean sample state, use the reset command above.
- If the API returns a validation error, inspect the source row: statuses must be `locked`, `active`, or `cleared`, and `hint_unlocked` must be `0` or `1`.