# Agile Project Plan — InterviewHub

**Method:** Scrum-style, **2 sprints of 2 weeks each**. Each sprint is divided into **4 parts, one per member**, so every member delivers a slice of their own module in every sprint.
**Tools:** GitHub Issues (user stories, bugs), GitHub Projects board (Backlog → Sprint → In progress → Review → Done), branches + pull requests with mandatory review, Jenkins/GitHub Actions for CI.

## 1. Roles
| Role | Who |
|------|-----|
| Product owner / Scrum master | Member 1 (Sprint 1), Member 3 (Sprint 2) |
| Developers | All four members, each owning one module end to end |
| Reviewer for each PR | Next member in the cycle (M1→M2→M3→M4→M1) |

## 2. Definition of Done
- Code merged to `main` through a reviewed PR linked to its user story.
- Unit tests written; CI green (lint, Bandit, tests, coverage ≥ 85%).
- API and docs updated; acceptance criteria demonstrated in sprint review.

## 3. Product backlog (user stories)
Story points use Fibonacci (1, 2, 3, 5, 8).

| ID | User story | Module | SP | Sprint | Req |
|----|-----------|--------|----|--------|-----|
| US-1.1 | As a student I want to register and log in so that my activity is saved. | M1 | 5 | 1 | FR-1.1, FR-1.2 |
| US-1.2 | As a student I want to edit my profile and target role so suggestions fit me. | M1 | 2 | 1 | FR-1.4 |
| US-1.3 | As a student I want to change my password so my account stays secure. | M1 | 2 | 1 | FR-1.5 |
| US-1.4 | As an admin I want to assign moderator roles and disable abusive accounts. | M1 | 3 | 2 | FR-1.6, FR-1.7 |
| US-1.5 | As the team we want security headers, token expiry and RBAC tests so the app passes security validation. | M1 | 3 | 2 | SR-1…SR-5 |
| US-2.1 | As a student I want to share my interview experience round by round so juniors can prepare. | M2 | 5 | 1 | FR-2.1, FR-2.2 |
| US-2.2 | As a student I want to filter experiences by company, role, outcome and year. | M2 | 3 | 1 | FR-2.4 |
| US-2.3 | As a moderator I want to approve or reject new posts to keep quality high. | M2 | 3 | 2 | FR-2.3 |
| US-2.4 | As a student I want to upvote helpful experiences so the best rise to the top. | M2 | 2 | 2 | FR-2.5 |
| US-2.5 | As a student I want company insights (selection rate, difficulty, top roles). | M2 | 3 | 2 | FR-2.7 |
| US-2.6 | As a student I want to post anonymously so I can be honest. | M2 | 1 | 1 | FR-2.1 |
| US-3.1 | As a student I want to browse and search a question bank by topic, difficulty and company. | M3 | 3 | 1 | FR-3.2 |
| US-3.2 | As a student I want to add questions I was asked so others benefit. | M3 | 2 | 1 | FR-3.1 |
| US-3.3 | As a student I want duplicate questions merged so the bank stays clean and shows how often a question is asked. | M3 | 5 | 1 | FR-3.3 |
| US-3.4 | As a student I want AI-ranked question suggestions for my company/role with reasons. | M3 | 8 | 2 | FR-3.4, FR-3.5 |
| US-3.5 | As a developer I want the suggestion engine behind an interface so we can plug in an LLM later. | M3 | 2 | 2 | FR-3.7 |
| US-4.1 | As a student I want a timed mock interview with questions for my target role. | M4 | 5 | 1 | FR-4.1, FR-4.5 |
| US-4.2 | As a student I want instant scoring and feedback on each answer. | M4 | 5 | 2 | FR-4.3 |
| US-4.3 | As a student I want to review completed sessions with key points revealed. | M4 | 2 | 1 | FR-4.4, FR-4.7 |
| US-4.4 | As a student I want a dashboard of my progress, weak topics and streak. | M4 | 5 | 2 | FR-4.6 |
| US-4.5 | As a student I want new sessions to focus on my weak topics. | M4 | 3 | 2 | FR-4.1 |
| US-0.1 | As the team we want CI (lint, security scan, tests, coverage) on every PR. | All | 3 | 1 | NFR-3, SR-10 |
| US-0.2 | As the team we want a Docker image and Jenkins pipeline for deployment. | All | 3 | 2 | NFR-6 |

**Velocity:** ~39 SP per 2-week sprint (~10 per member per sprint).

## 4. Sprint plan (2 sprints × 4 parts)

### Sprint 1 — Foundation & core flows (Weeks 1–2)
**Sprint goal:** every module has its data model, core API, first UI screen and tests; CI runs on every PR.
**Documents due:** Synopsis, SRS, Validation Spec v1 (planning), HLD, LLD, Validation Spec v2 (after design).

| Part | Member | Module | Stories | SP | Deliverable at sprint review |
|------|--------|--------|---------|---:|------------------------------|
| 1A | Member 1 | Auth & users | US-1.1 Register/login, US-1.2 Profile, US-1.3 Change password, US-0.1 CI pipeline | 12 | Login works end to end; GitHub Actions + Jenkinsfile run lint, Bandit and tests |
| 1B | Member 2 | Experiences | US-2.1 Share experience, US-2.2 Filter/sort, US-2.6 Anonymous posts | 9 | Students can post and browse experiences by company/role |
| 1C | Member 3 | Question bank | US-3.1 Browse/search, US-3.2 Add question, US-3.3 Duplicate merging | 10 | Searchable bank; reworded duplicates merge and show "asked N×" |
| 1D | Member 4 | Mock interview | US-4.1 Timed mock interview, US-4.3 Review sessions | 7 | Start a timed session, answer, finish and review it |
| | | | **Sprint 1 total** | **38** | |

**Week-by-week (all parts in parallel):**
| Week | Focus |
|------|-------|
| 1 | Requirements & design: SRS, use cases, HLD module interfaces frozen, LLD class/ER diagrams; models + schemas for each module |
| 2 | Services, REST endpoints, UI screens, unit tests; first PRs merged in order M1 → M3 → M2 → M4 |

### Sprint 2 — Intelligence, analytics & release (Weeks 3–4)
**Sprint goal:** AI suggestions, scoring and analytics complete; security hardened; app deployable with Docker/Jenkins.
**Documents due:** Unit test & coverage report, Validation Spec v3 (after implementation), System validation report, Maintenance plan, Demo script.

| Part | Member | Module | Stories | SP | Deliverable at sprint review |
|------|--------|--------|---------|---:|------------------------------|
| 2A | Member 1 | Auth & users | US-1.4 Admin roles & deactivation, US-1.5 Security hardening & pen tests | 6 | RBAC + all 13 penetration test cases passing |
| 2B | Member 2 | Experiences | US-2.3 Moderation queue, US-2.4 Upvotes, US-2.5 Company insights, US-0.2 Docker & deploy | 11 | Moderated content, company insight page, `docker compose up` works |
| 2C | Member 3 | AI suggestions | US-3.4 AI question suggestions, US-3.5 Pluggable provider | 10 | Ranked, explained suggestions; LLM-ready interface |
| 2D | Member 4 | Scoring & analytics | US-4.2 Answer scoring & feedback, US-4.4 Dashboard, US-4.5 Weak-topic focus | 13 | Instant feedback, progress dashboard, weak topics steer next session |
| | | | **Sprint 2 total** | **40** | |

**Week-by-week:**
| Week | Focus |
|------|-------|
| 3 | Feature implementation + unit tests (coverage ≥ 85%), SonarQube/Bandit fixes |
| 4 | System validation (usage scenarios), bug fixing, documentation, demo rehearsal, release v1.0.0 |

### Story points per member
| Member | Sprint 1 | Sprint 2 | Total |
|--------|---------:|---------:|------:|
| Member 1 | 12 | 6 | 18 |
| Member 2 | 9 | 11 | 20 |
| Member 3 | 10 | 10 | 20 |
| Member 4 | 7 | 13 | 20 |

## 5. Ceremonies
| Ceremony | When | Output |
|----------|------|--------|
| Sprint planning | Day 1 of each sprint | Stories moved to sprint column, tasks split into the 4 parts |
| Daily stand-up (async in WhatsApp/GitHub discussion) | Daily | Yesterday / today / blockers |
| Code review | Each PR | ≥ 1 approval, CI green |
| Sprint review | Last day of each sprint (end of Week 2 and Week 4) | Demo of done stories to faculty/TA |
| Retrospective | After each sprint review | 1 thing to keep, 1 to change |

## 6. Branching & PR workflow
Every member opens **one pull request per sprint** (8 PRs in total). Within a sprint, PRs merge in the order M1 → M3 → M2 → M4 because each part builds on the previous one.

| Round | Sprint / part | Branch | Author | Reviewer |
|------:|---------------|--------|--------|----------|
| 1 | Sprint 1 · 1A | `feature/s1-m1-auth` | Member 1 | Member 2 |
| 2 | Sprint 1 · 1C | `feature/s1-m3-question-bank` | Member 3 | Member 4 |
| 3 | Sprint 1 · 1B | `feature/s1-m2-experiences` | Member 2 | Member 3 |
| 4 | Sprint 1 · 1D | `feature/s1-m4-mock-interview` | Member 4 | Member 1 |
| 5 | Sprint 2 · 2A | `feature/s2-m1-auth` | Member 1 | Member 2 |
| 6 | Sprint 2 · 2C | `feature/s2-m3-question-bank` | Member 3 | Member 4 |
| 7 | Sprint 2 · 2B | `feature/s2-m2-experiences` | Member 2 | Member 3 |
| 8 | Sprint 2 · 2D | `feature/s2-m4-mock-interview` | Member 4 | Member 1 |

`main` is protected and always green. Commit message style: `feat(module): ...`, `fix(...)`, `test(...)`, `docs(...)`, `ci: ...`.

## 7. Risk register
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Module interface changes break others | M | H | Interfaces frozen at end of Sprint 1 Week 1 (HLD §4); owners of both modules review |
| Spam / low-quality posts | M | M | Moderation queue, upvotes, validation |
| Scoring seen as unfair | M | M | Combine auto score with self-rating; show covered/missed points transparently |
| Member unavailable | L | M | Every module has a documented API and tests; reviewer knows the code |
| Merge conflicts on shared files | M | L | Shared files (`main.py`, `database.py`, `app.js`, `index.html`) change by one line per module; merge in order M1 → M3 → M2 → M4 |
