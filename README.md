# Fidant.AI Analytics

**Stack:** React (Frontend) + Node.js (Gateway API) + Python FastAPI (Analytics) + PostgreSQL (DB)

Fidant.AI provides usage statistics for users' AI interactions.
- Only **committed** events are counted
- **Reserved** events are shown separately (last 15 minutes)
- Daily statistics are provided
- Daily limits are applied based on subscription plan

---

## Project Structure

```
fidant_analytics/
├─ python-service/        # FastAPI Analytics Service
│  ├─ main.py
│  ├─ db.py
│  └─ models.py
├─ node-gateway/          # Node.js API Gateway
│  └─ server.js
└─ frontend/              # React Frontend
   └─ src/App.js
```

---

## Installation and Run (Windows)

### 1️⃣ Python FastAPI (Analytics Service)

1. Create and activate virtual environment:
```cmd
cd python-service
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```cmd
pip install fastapi uvicorn sqlalchemy psycopg2-binary
```

3. PostgreSQL setup:
- Database: `fidant_db`
- User/password: adjust according to your PostgreSQL setup
- Update `DATABASE_URL` in `db.py`

4. Run the server:
```cmd
uvicorn main:app --reload --port 8000
```

Check: [http://127.0.0.1:8000/analytics](http://127.0.0.1:8000/analytics)

---

### 2️⃣ Node.js Gateway

1. Install dependencies:
```cmd
cd node-gateway
npm install express axios
```

2. Run the server:
```cmd
node server.js
```

The gateway calls Python FastAPI `/analytics` endpoint.

---

### 3️⃣ React Frontend

1. Install dependencies:
```cmd
cd frontend
npm install
npm install axios
```

2. Run the frontend:
```cmd
npm start
```

Check: [http://localhost:3000](http://localhost:3000)

---

## Endpoint Summary

**GET /analytics**
- Parameter: `days` (1~90, default 7)
- Example Response:
```json
{
  "plan": "starter",
  "daily_limit": 30,
  "period": { "from": "2026-03-27", "to": "2026-04-02" },
  "days": [
    { "date":"2026-04-02", "committed":12, "reserved":2, "limit":30, "utilization":0.4 }
  ],
  "summary": {
    "total_committed": 87,
    "avg_daily": 12.4,
    "peak_day": { "date":"2026-03-30", "count":28 },
    "current_streak": 5
  }
}
```

- `committed`: actual AI usage
- `reserved`: recent reserved turns (15 minutes)
- `utilization`: committed / limit ratio
- Days without events return zero values

---

## Development Environment

- Windows 10+
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Browser: Chrome / Edge

---

## Extension Ideas

- Redis caching for performance
- Implement reserve / commit APIs
- Add JWT authentication on Gateway
- Display usage charts in frontend (Chart.js / Recharts)

