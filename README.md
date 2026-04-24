# SkillBridge Attendance Management API

A REST API backend for a fictional state-level skilling programme called SkillBridge, built as part of a Python Developer Intern assignment.

---

## Tech Stack

- **Framework:** Django + Django REST Framework
- **Database:** SQLite (local) / PostgreSQL (production)
- **Authentication:** JWT (via PyJWT)
- **Testing:** pytest + pytest-django

I chose Django over the recommended FastAPI because I'm more productive with it — I could build, test, and document the full system within the 3-day window. The REST API design and JWT implementation are framework-agnostic and follow the same principles either way.

---

## Project Structure

```
skillbridge/
├── config/                  # Django project settings and root URLs
│   ├── settings.py
│   └── urls.py
├── users/                   # Auth, user model, JWT, permissions
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── authentication.py    # Custom JWT auth class
│   ├── permissions.py       # Role-based permission classes
│   └── exceptions.py        # Custom error handler
├── attendance/              # Batches, sessions, attendance
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── management/
│       └── commands/
│           └── seed_data.py
├── tests/
│   └── test_api.py
├── manage.py
├── requirements.txt
├── .env.example
├── pytest.ini
├── conftest.py
└── README.md
```

---

## Features Implemented

- User signup and login with hashed passwords
- JWT authentication with role embedded in token
- Five user roles with strict server-side access control: `student`, `trainer`, `institution`, `programme_manager`, `monitoring_officer`
- Batch creation, invite link generation, student joining via token
- Session creation by trainers
- Attendance marking by students (only for sessions they are enrolled in)
- Attendance summary endpoints for institution and programme manager roles
- Monitoring officer dual-token system — standard login token + API key required to get a short-lived scoped token
- Custom exception handler — foreign key errors return 404, validation errors return 422
- Seed script that creates 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions with attendance records
- 5 pytest tests hitting a real in-memory SQLite database

---

## API Endpoints

| Method | Endpoint | Who |
|--------|----------|-----|
| POST | `/auth/signup` | All roles |
| POST | `/auth/login` | All roles |
| POST | `/auth/monitoring-token` | Monitoring officer only |
| GET | `/auth/me` | Authenticated user |
| POST | `/batches` | Trainer, Institution |
| POST | `/batches/{id}/invite` | Trainer |
| POST | `/batches/join` | Student |
| GET | `/batches/{id}/summary` | Institution |
| POST | `/sessions` | Trainer |
| GET | `/sessions/{id}/attendance` | Trainer |
| POST | `/attendance/mark` | Student |
| GET | `/institutions/{id}/summary` | Programme Manager |
| GET | `/programme/summary` | Programme Manager |
| GET | `/monitoring/attendance` | Monitoring Officer (scoped token) |

Every protected endpoint reads the caller's role from their JWT and returns 403 if the role is not permitted. Access control is enforced entirely server-side.

---

## JWT Token Structure

**Standard token** — issued to all roles on login, valid for 24 hours:
```json
{
  "user_id": 5,
  "role": "trainer",
  "token_type": "standard",
  "iat": 1710000000,
  "exp": 1710086400
}
```

**Monitoring scoped token** — issued only after presenting a valid standard token AND the correct API key, valid for 1 hour:
```json
{
  "user_id": 12,
  "role": "monitoring_officer",
  "token_type": "monitoring",
  "iat": 1710000000,
  "exp": 1710003600
}
```

The `IsMonitoringOfficer` permission class rejects any token where `token_type` is not `"monitoring"` — even if the user's role is correct.

---

## Local Setup

Assumes Python and pip are already installed.

**1. Clone the repository**
```bash
git clone https://github.com/triveni-gavathe/skillbridge-api.git
cd skillbridge
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create your `.env` file**
```bash
cp .env.example .env
```

Open `.env` and fill in your own `SECRET_KEY`. Everything else can stay as-is for local development.

**5. Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**6. Seed the database**
```bash
python manage.py seed_data
```

**7. Start the server**
```bash
python manage.py runserver
```

API is now live at `http://127.0.0.1:8000`

---

## Running Tests

```bash
pytest
```

For detailed output:
```bash
pytest -v
```

All 5 tests run against a real in-memory SQLite database — nothing is fully mocked.

---

## Test Accounts

All seeded accounts use the password: `pass1234`

| Role | Email |
|------|-------|
| Student | student1@test.com |
| Trainer | trainer1@test.com |
| Institution | admin1@test.com |
| Programme Manager | pm@test.com |
| Monitoring Officer | monitor@test.com |

**Monitoring Officer API Key** (for `/auth/monitoring-token`):
```
test-monitoring-key-123
```

---

## Sample curl Commands

**Signup**
```bash
curl -X POST http://127.0.0.1:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"pass1234","role":"student"}'
```

**Login**
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"trainer1@test.com","password":"pass1234"}'
```

**Create session (trainer)**
```bash
curl -X POST http://127.0.0.1:8000/sessions \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"batch":1,"title":"Day 1","date":"2024-03-01","start_time":"10:00:00","end_time":"12:00:00"}'
```

**Get monitoring scoped token — Step 1: login**
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"monitor@test.com","password":"pass1234"}'
```

**Get monitoring scoped token — Step 2: exchange**
```bash
curl -X POST http://127.0.0.1:8000/auth/monitoring-token \
  -H "Authorization: Bearer <standard_token>" \
  -H "Content-Type: application/json" \
  -d '{"key":"test-monitoring-key-123"}'
```

**Use scoped token**
```bash
curl http://127.0.0.1:8000/monitoring/attendance \
  -H "Authorization: Bearer <monitoring_token>"
```

---

## Schema Decisions

**`batch_trainers` (many-to-many through table)**
A batch can have multiple trainers and a trainer can work across multiple batches. I used an explicit through model `BatchTrainer` instead of Django's implicit M2M so it is easier to add fields like `assigned_at` later without a migration headache.

**`batch_invites`**
Instead of sharing a batch ID directly (which anyone could guess), trainers generate a UUID token with an expiry. The student sends the token to `/batches/join`. Once used, the token is marked as `used=True` so it cannot be reused. This prevents unauthorized students from joining batches.

**Dual-token for Monitoring Officer**
The standard JWT proves identity. The scoped token proves the user also possesses the API key — a second factor that limits access to read-only monitoring endpoints only. The scoped token expires in 1 hour vs 24 hours for standard tokens, reducing the risk window if it leaks.

---

## Deployment

The API is not deployed at this time.

I attempted to deploy to Render but ran into a database configuration issue with the PostgreSQL connection string during the `migrate` step in the build process. Rather than submit a broken live URL, I decided to document this honestly.

Everything works correctly locally. The full API can be run with `python manage.py runserver` after following the setup steps above. All endpoints, role checks, and both token flows are functional and testable locally or via the test suite.

If given more time I would fix the deployment by switching to `dj-database-url` for connection string parsing and ensuring migrations run cleanly in the Render build pipeline.

---

## What is Working

- All auth endpoints (signup, login, monitoring token exchange)
- All 14 endpoints with correct role-based access control
- JWT generation, decoding, and validation
- Dual-token system for monitoring officer
- Attendance marking with enrollment check
- Invite token generation and joining flow
- All summary endpoints
- 405 on non-GET requests to `/monitoring/attendance`
- Custom error responses (401, 403, 404, 422)
- Database seed script
- 5 pytest tests passing

## What is Incomplete

- Deployment — not live (explained above)
- Token revocation — currently there is no blacklist. Tokens are valid until they expire.
- Pagination on list endpoints

---

## Security Issues and Notes

**Current issue:** Tokens cannot be revoked. If a token is stolen, it remains valid until it expires (24h standard, 1h monitoring). In a real deployment I would add a token blacklist table — on logout, the token's `jti` (JWT ID) is stored, and every request checks this table before proceeding. Redis would work well for this given its TTL support.

**Token rotation in production:** Rotate `SECRET_KEY` periodically. All existing tokens would be invalidated instantly since they cannot be verified against the new key. Issue new tokens to users by requiring re-login.

---

## What I Would Do Differently

If I had more time I would switch to FastAPI. Not because Django was wrong for this task, but because FastAPI's automatic OpenAPI docs (`/docs`) would let reviewers explore and test every endpoint directly in the browser without needing Postman — a much better experience for an assignment submission.

---

## Challenges

The most challenging part was the dual-token system for the monitoring officer. Getting the permission class to distinguish between a standard JWT and a monitoring-scoped JWT — and making sure the standard token was cleanly rejected even when the role matched — required careful design of the `token_type` field and the `JWTAuthentication` class that attaches it to the request object.
