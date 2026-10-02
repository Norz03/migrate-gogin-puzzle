# Puzzle Tower API

The local API accepts room state from the SQLite migration and stores the latest state per room ID.

## `GET /health`

Returns `200 OK` with `{"status":"ok"}` when the service is ready.

## `POST /api/v1/sync`

Synchronizes one room. This is an upsert: sending the same ID again replaces its state instead of creating a duplicate.

```json
{"room_id": 1, "status": "active", "hint_unlocked": 1}
```

`room_id` must be positive, `status` must be `locked`, `active`, or `cleared`, and `hint_unlocked` must be `0` or `1`. All fields are required; additional fields are rejected.

Responses:

- `202 Accepted`: state persisted successfully; response body is the stored room.
- `400 Bad Request`: malformed, incomplete, or invalid room payload.
- `405 Method Not Allowed`: request method is not `POST`.
- `500 Internal Server Error`: destination state could not be persisted.

## `GET /api/v1/rooms`

Returns the current destination state as an array sorted by `room_id`. The API persists this state to the file configured by `TOWER_STATE_PATH`.