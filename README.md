# Fidant Analytics

Usage analytics dashboard for Fidant.AI — tracks daily turn consumption per user across plan tiers.

---

## Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React 18 + TypeScript + Chart.js
- **Auth**: JWT (python-jose)
- **DB tooling**: Prisma (schema + migrations), SQLAlchemy (runtime ORM)

---

## Running locally

### 1. Start PostgreSQL

```bash
cd fidant_analytics
docker-compose up -d
```

### 2. Run the migration

```bash
cd fidant_analytics/python-service
psql postgresql://admin:secret@localhost:5432/mydb -f prisma/migrations/20260402205723_add_daily_usage_cache/migration.sql
```

### 3. Start the backend

```bash
cd fidant_analytics/python-service
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then fill in values
uvicorn src.main:app --reload --port 5000
```

Seed a test user (first run only):

```
GET http://localhost:5000/seed-user
```

### 4. Start the frontend

```bash
cd fidant-dashboard
npm install
npm start
```

Open http://localhost:3000 and log in with `test@test.com`.

---

## Environment variables

See `fidant_analytics/python-service/.env.example`:

| Variable       | Description                        |
|----------------|------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string       |
| `SECRET_KEY`   | JWT signing secret (keep private)  |

---

## Architecture notes

### Cache strategy (`daily_usage_cache`)

The stats endpoint avoids a full scan of `daily_usage_events` on every request:

- **Past days** are cached indefinitely — committed counts for past dates never change.
- **Today's row** is refreshed if `cached_at` is older than 5 minutes (TTL).
- On a cache miss the endpoint falls back to querying raw events and writes the result to cache (upsert).

### Reserved turns

Only `status = "committed"` events count toward usage. `status = "reserved"` events are shown separately, but only if `reserved_at` is within the last 15 minutes — stale reservations are excluded.

---

## What I'd do differently with more time

- Add a background worker (e.g. APScheduler or Celery beat) to pre-warm the cache at midnight instead of lazy population on first request.
- Replace the email-only login with a proper auth flow (password hash or magic link).
- Add pagination / configurable `days` selector in the UI.
- Write unit tests for the cache fallback logic and streak calculation.
- Use React Query instead of raw `useEffect` for data fetching (caching, refetch on focus, etc.).
