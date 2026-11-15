# High-Level Architecture Document — InterviewHub

## 1. Architectural style
A **modular monolith** with a **layered architecture** inside each module:

```
Router (HTTP, FastAPI)  →  Service (business rules)  →  Model (SQLAlchemy ORM)  →  Database
          ↑ Schemas (Pydantic contracts validate every request/response)
```

Why a modular monolith and not microservices: a 4-person team, one database, and a one-semester timeline. Module boundaries are still strict (each module exposes a small service API), so a module could be split into a service later.

## 2. System context
```mermaid
flowchart LR
  U[Student / Moderator / Admin<br/>Browser] -- HTTPS JSON --> API[InterviewHub API<br/>FastAPI]
  API --> DB[(SQL Database<br/>SQLite / PostgreSQL)]
  API -- serves --> SPA[Static SPA<br/>HTML/CSS/JS]
  CI[Jenkins / GitHub Actions] -- build, test, scan --> IMG[Docker image]
  IMG -- deploy --> API
  SQ[SonarQube] -. quality gate .- CI
```

## 3. Module decomposition
```mermaid
flowchart TB
  subgraph Core[app/core — shared]
    CFG[config] --- DBM[database] --- ERR[errors] --- TXT[text utils]
  end
  subgraph M1[M1 Auth & Users]
    A1[router] --> A2[service] --> A3[models: User]
    A4[deps: get_current_user, require_roles]
    A5[security: bcrypt, JWT]
  end
  subgraph M2[M2 Experiences & Companies]
    E1[router] --> E2[service] --> E3[models: Experience, Round, Vote]
    C1[companies service] --> C2[Company]
  end
  subgraph M3[M3 Question Bank & AI]
    Q1[router] --> Q2[service] --> Q3[models: Question]
    Q4[recommender: TF-IDF engine]
  end
  subgraph M4[M4 Mock Interview & Analytics]
    P1[router] --> P2[service] --> P3[models: Session, Item]
    P4[scorer]
  end
  E2 -- create questions --> Q2
  P2 -- pick questions --> Q2
  Q2 --> Q4
  P2 --> P4
  E2 --> C1
  Q2 --> C1
  E1 & Q1 & P1 -. auth .-> A4
```

### Dependency rules
- Modules depend on **core** and on other modules only through their `service` functions or `auth.deps`.
- No circular dependencies: `auth ← companies ← questions ← experiences`, `questions ← practice`.
- Services raise domain errors (`app/core/errors.py`); one handler maps them to HTTP status codes, so services can be unit tested without HTTP.

## 4. Interface definitions between modules (API stability contract)
| Provider | Function | Consumer | Purpose |
|----------|----------|----------|---------|
| M1 | `get_current_user`, `get_optional_user`, `require_roles(*roles)` | M2, M3, M4 routers | Authentication & authorisation |
| M2 (companies) | `get_or_create(db, name)`, `find_by_name`, `slugify` | M2, M3 | Shared company catalogue |
| M3 | `create(db, QuestionCreate, author, source_experience_id, commit)` → `(Question, created)` | M2 | Feed asked questions into bank |
| M3 | `suggest(db, Query)` → `[(Question, score, reason)]` | M4 | Select interview questions |
| M3 | `recommender.SuggestionProvider` protocol | Future LLM provider | Extensibility |
| M4 | `analytics(db, user)` → `Analytics` | M4 `start()` | Weak-topic feedback loop |

These signatures are frozen at the end of Sprint 1, Week 1; changes require a PR reviewed by both affected owners.

## 5. Data architecture
```mermaid
erDiagram
  USERS ||--o{ EXPERIENCES : writes
  USERS ||--o{ EXPERIENCE_VOTES : casts
  USERS ||--o{ QUESTIONS : adds
  USERS ||--o{ PRACTICE_SESSIONS : takes
  COMPANIES ||--o{ EXPERIENCES : about
  COMPANIES ||--o{ QUESTIONS : asked_at
  EXPERIENCES ||--o{ EXPERIENCE_ROUNDS : has
  EXPERIENCES ||--o{ EXPERIENCE_VOTES : receives
  EXPERIENCES ||--o{ QUESTIONS : sources
  PRACTICE_SESSIONS ||--o{ SESSION_ITEMS : contains
  QUESTIONS ||--o{ SESSION_ITEMS : used_in
```

## 6. UI/UX design
- Single-page app with hash routing; top navigation: **Experiences · Question Bank · Mock Interview · Dashboard · (Moderation)**.
- Design principles: one primary action per screen (blue button), card layout, colour-coded pills (green = selected/easy, amber = pending/medium, red = rejected/hard), toasts for feedback.
- Accessibility: semantic HTML, labelled inputs, sufficient contrast, keyboard-submittable forms, SVG chart has an `aria-label`.
- Flow to start practising after login: Mock Interview → Start interview (2 clicks, meets NFR-4).

| Screen | Purpose | Owner |
|--------|---------|-------|
| Login / Register / Profile | Account management | M1 |
| Experiences list, Share form, Company insights, Moderation | Crowdsourced experiences | M2 |
| Question bank, AI suggestions, Add question | Question bank | M3 |
| Mock interview setup, live session, review, Dashboard | Practice & analytics | M4 |

## 7. Deployment architecture
```mermaid
flowchart LR
  Dev[Developer] -- push / PR --> GH[GitHub repo]
  GH -- webhook --> J[Jenkins]
  GH -- PR check --> GA[GitHub Actions]
  J --> L[Lint] --> S[Bandit + pip-audit] --> T[pytest + coverage] --> SQ[SonarQube] --> D[Docker build] --> STG[Staging container :8000]
```
The container runs as a non-root user, stores the SQLite file on a volume (`/data`) and exposes `/api/health` for health checks.

## 8. Cross-cutting concerns
| Concern | Approach |
|---------|----------|
| Configuration | `app/core/config.py`, environment variables only |
| Error handling | Domain exceptions → single JSON error handler |
| Security | JWT, bcrypt, role checks, object-level ownership checks, input schemas, output escaping, security headers |
| Logging | Uvicorn access logs; Jenkins archives test, coverage and Bandit reports |
| Testability | Dependency-injected DB session; pure functions for scoring and ranking |
