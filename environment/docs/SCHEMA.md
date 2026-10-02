# Source Database Schema

The migration reads `data/tower.sql` as a SQLite database in read-only mode. `scripts/init_db.py` creates the sample database and seeds rooms 1 through 3 without overwriting existing rows.

## `rooms`

| Column | Type | Constraints | Meaning |
| --- | --- | --- | --- |
| `room_id` | INTEGER | Primary key | Unique room identifier |
| `status` | TEXT | `locked`, `active`, or `cleared` | Current room state |
| `hint_unlocked` | INTEGER | `0` or `1` | Whether the room hint is unlocked |

Rows are read in ascending `room_id` order. The migration does not mutate or delete source data; destination writes are handled by the Go API.