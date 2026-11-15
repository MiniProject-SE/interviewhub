# System Validation Report & Maintenance Plan — InterviewHub

## Part A — System Validation Report

### A.1 Approach
System validation was **usage-driven**: each scenario from Validation Spec §6 was executed against the running application (`uvicorn` with seeded demo data, and the Docker image), combining **black-box** testing through the UI with **white-box** checks of database state and API responses. A Playwright smoke script drove the main UI flows to catch JavaScript errors.

### A.2 Results
| SV ID | Scenario | Result | Notes |
|-------|----------|--------|-------|
| SV-1 | New student onboarding | Pass | Empty dashboard links to mock interview |
| SV-2 | Share experience → moderator approves | Pass | Questions appear in bank with source experience |
| SV-3 | Duplicate question contribution | Pass | "Merged" toast; asked count increments |
| SV-4 | Company prep via insights page | Pass | Practice link pre-fills company |
| SV-5 | Weak-topic practice loop | Pass | After a low OS score, next session started with an OS question first |
| SV-6 | Timer expiry | Pass | Session becomes *expired*, answers rejected (409) |
| SV-7 | Student opens moderation | Pass | Nav link hidden; API returns 403 |
| UI smoke | Login → experiences → practice → answer → finish → dashboard → suggestions | Pass | 0 JavaScript errors |

### A.3 Security validation summary
All 13 penetration test cases (PT-1 … PT-13) pass. Bandit reports no medium/high issues. Container runs as non-root. Secrets via environment.

### A.4 Known limitations
| Limitation | Impact | Planned action |
|-----------|--------|----------------|
| Keyword scoring cannot judge correctness of reasoning | Score is a guide, not a grade | Optional LLM provider (v1.2) |
| SQLite in single container | Not suitable for many concurrent writers | Switch `DATABASE_URL` to PostgreSQL for production |
| No email verification / password reset | Anyone can register any email | Add verified email flow (v1.1) |
| Suggestion index rebuilt per request | Fine to ~10k questions | Cache index, invalidate on write (v1.1) |

## Part B — Maintenance Plan

### B.1 Maintenance types
| Type | Examples for InterviewHub | Process |
|------|---------------------------|---------|
| Corrective | Bug reports from students (wrong score, broken filter) | GitHub issue (bug template) → failing test first → fix PR → patch release |
| Adaptive | New Python/FastAPI versions, moving to PostgreSQL, new company names | Dependabot / pip-audit alerts, quarterly upgrade sprint |
| Perfective | New topics, better ranking weights, UI improvements | Backlog user stories, prioritised each sprint |
| Preventive | Refactoring, raising coverage, index caching | 20% of each sprint reserved for tech debt |

### B.2 Release & versioning
- Semantic versioning: `MAJOR.MINOR.PATCH`; `/api/health` reports the version.
- `main` is always deployable; tags `v1.0.0`, `v1.0.1` … trigger the Jenkins deploy stage.
- API changes are additive within a major version (LLD §6).

### B.3 Monitoring & operations
| What | How |
|------|-----|
| Liveness | Docker `HEALTHCHECK` on `/api/health` |
| Errors | Uvicorn logs; 5xx count reviewed weekly |
| Data backup | Nightly copy of the `/data` volume (SQLite file) or `pg_dump` in production; keep 7 days |
| Content quality | Moderators clear the pending queue at least every 48 hours |
| Security | pip-audit + Bandit on every build; rotate `JWT_SECRET` each semester |

### B.4 Ownership after hand-over
| Area | Primary | Backup |
|------|---------|--------|
| Auth, security, CI pipeline | Member 1 | Member 4 |
| Experiences, companies, moderation, Docker, seed data | Member 2 | Member 1 |
| Question bank, recommender, SonarQube | Member 3 | Member 2 |
| Practice, scoring, analytics, GitHub Actions | Member 4 | Member 3 |

### B.5 Roadmap
| Version | Items |
|---------|-------|
| v1.1 | Email verification, password reset, cached suggestion index, comments on experiences |
| v1.2 | Optional LLM provider for suggestions and answer feedback (via `SuggestionProvider`) |
| v1.3 | Peer mock interviews, export of practice report as PDF, placement-cell admin analytics |
