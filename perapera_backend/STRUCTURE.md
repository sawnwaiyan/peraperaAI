# Backend Structure — AI English App
## FastAPI + PostgreSQL + Alembic

Files marked ★ exist now. Others are added as each feature is built.
Max 200–250 lines per file — split when over.

---

## Current State: Day 1 Skeleton

```
backend/
├── main.py                  ★  FastAPI entry point (~20 lines)
├── requirements.txt         ★  All Python dependencies
├── Dockerfile               ★  Python 3.12-slim image
├── .env                     ★  Local secrets — never committed
├── .env.example             ★  Template — committed to git
└── STRUCTURE.md             ★  This file
```

---

## Target State: Release 1.0 Complete

Add files only when you start that feature. Do not pre-create empty files.

```
backend/
├── main.py                            ★  (FastAPI app entry, ~30 lines)
├── config.py                             (pydantic-settings, ~50 lines)        [Week 1]
├── requirements.txt                   ★
├── Dockerfile                         ★
├── .env                               ★
├── .env.example                       ★
├── STRUCTURE.md                       ★
│
├── alembic.ini                           (auto-generated: alembic init alembic) [Week 1]
├── alembic/                              (auto-generated)                       [Week 1]
│   ├── env.py                            (edit for async + Base.metadata)
│   └── versions/                         (migration files live here)
│
├── core/                                 (shared infrastructure)                [Week 1]
│   ├── __init__.py
│   ├── database.py                       (async engine + session, ~40 lines)
│   ├── dependencies.py                   (get_db, get_current_user, ~50 lines)
│   ├── security.py                       (JWT + password hashing, ~80 lines)
│   └── exceptions.py                     (custom HTTP errors in Japanese, ~40 lines)
│
├── models/                               (SQLAlchemy table definitions)
│   ├── __init__.py
│   ├── user.py                        ★  (~60 lines)                            [Week 1]
│   ├── mission.py                        (~50 lines)                            [Week 2]
│   ├── mission_result.py                 (~50 lines)                            [Week 2]
│   ├── deleted_account.py                (~30 lines)                            [Week 4]
│   └── device_registry.py                (~30 lines)                            [Week 4]
│
├── schemas/                              (Pydantic request/response shapes)
│   ├── __init__.py
│   ├── auth.py                           (~40 lines)                            [Week 1]
│   ├── user.py                           (~80 lines)                            [Week 1]
│   ├── mission.py                        (~60 lines)                            [Week 2]
│   └── mission_result.py                 (~50 lines)                            [Week 2]
│
├── routers/                              (API endpoints — one file per feature)
│   ├── __init__.py
│   ├── auth.py                           (register, login, refresh, ~150 lines) [Week 1]
│   ├── users.py                          (profile, session count, ~100 lines)   [Week 4]
│   ├── missions.py                       (CRUD + generation, ~120 lines)        [Week 2]
│   ├── results.py                        (save + fetch results, ~100 lines)     [Week 2]
│   ├── voice.py                          (STT/TTS proxy, ~100 lines)            [Week 3]
│   └── openai_proxy.py                   (free session GPT proxy, ~80 lines)    [Week 4]
│
├── services/                             (business logic — routers never touch DB directly)
│   ├── __init__.py
│   ├── auth_service.py                   (register/login logic, ~120 lines)     [Week 1]
│   ├── user_service.py                   (session counting, profile, ~80 lines) [Week 4]
│   ├── mission_service.py                (mission CRUD, ~100 lines)             [Week 2]
│   ├── result_service.py                 (save/fetch results, ~80 lines)        [Week 2]
│   ├── stt_service.py                    (Whisper wrapper, ~60 lines)           [Week 3]
│   ├── tts_service.py                    (TTS wrapper, ~60 lines)               [Week 3]
│   └── openai_proxy_service.py           (dev key proxy, ~80 lines)             [Week 4]
│
└── utils/                                (small pure helpers)
    ├── __init__.py
    ├── validators.py                     (email/phone detect, ~40 lines)        [Week 1]
    └── phone_formatter.py                (+81 normalization, ~20 lines)         [Week 1]
```

---

## Build Order

| Week | Feature | What to create |
|------|---------|----------------|
| **Week 1** | Auth (register + login) | `config.py`, `core/*`, `models/user.py`, `schemas/auth.py`, `schemas/user.py`, `routers/auth.py`, `services/auth_service.py`, `utils/*`, Alembic init |
| **Week 2** | Missions + Results | `models/mission.py`, `models/mission_result.py`, `schemas/mission.py`, `schemas/mission_result.py`, `routers/missions.py`, `routers/results.py`, `services/mission_service.py`, `services/result_service.py` |
| **Week 3** | Voice (STT/TTS) | `routers/voice.py`, `services/stt_service.py`, `services/tts_service.py` |
| **Week 4** | OpenAI proxy + abuse prevention | `routers/openai_proxy.py`, `routers/users.py`, `services/openai_proxy_service.py`, `services/user_service.py`, `models/deleted_account.py`, `models/device_registry.py` |

---

## Router → User Flow Screen Mapping

| Router | Screens it serves | Key endpoints |
|--------|------------------|---------------|
| `auth.py` | A3 Register, A4 Profile, A5 Login | `POST /register`, `POST /login`, `POST /refresh` |
| `users.py` | D3 Settings | `GET /me`, `PATCH /me`, `DELETE /me` |
| `missions.py` | B3 Mission Selection, C1 Briefing | `POST /generate`, `GET /`, `GET /{id}` |
| `results.py` | C4 Review, D2 Progress | `POST /`, `GET /user/me` |
| `voice.py` | C2 Prepare, C3 Practice | `POST /stt`, `POST /tts` |
| `openai_proxy.py` | B2 Interview, C3 Practice (free sessions) | `POST /chat` |

---

## Rules

1. **Router → Service → DB**. Routers never touch the database directly.
2. **One file per feature**, max 200–250 lines. Split if over.
3. **Create files only when you start that feature.**
4. **All error messages in Japanese** — they surface in the Flutter app.
5. **Alembic for every schema change** — never ALTER TABLE manually.
6. **Secrets via .env only** — never hardcode keys or passwords.