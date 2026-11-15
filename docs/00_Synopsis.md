# Synopsis — InterviewHub

**Course:** UE24CS341A Software Engineering — Jackfruit Mini-Project
**Project ID 18:** Student's Interview Experience, Interview Question Bank and Practice Platform
**Team:** 4 members (see [08_Work_Division.md](08_Work_Division.md))

## 1. Problem statement
Students preparing for placements depend on scattered WhatsApp forwards, senior notes and generic websites. Interview experiences are not organised by company and role, the same questions get re-posted many times, and students have no structured way to practise or measure their improvement.

## 2. Proposed solution
**InterviewHub** is a crowdsourced web platform where students:

1. **Share interview experiences** organised by company, role, year and outcome, round by round.
2. **Build a shared question bank** automatically: every question mentioned in an experience is added to the bank, and near-duplicates are merged so popular questions rise to the top.
3. **Get AI-based question suggestions** ranked for their target company, role, topic and weak areas.
4. **Take timed mock interviews**, get instant keyword-coverage scoring and feedback, and **track performance** over time on a personal dashboard.

## 3. Feature list
| # | Feature | Module |
|---|---------|--------|
| 1 | Registration, login (JWT), profiles, password change | M1 Auth |
| 2 | Role-based access: student, moderator, admin; admin user management | M1 Auth |
| 3 | Post experiences with rounds, tips, outcome, difficulty, anonymous option | M2 Experiences |
| 4 | Browse/search/filter experiences by company, role, outcome, year; sort by recent or most helpful | M2 Experiences |
| 5 | Upvote helpful experiences; moderation queue (approve/reject) | M2 Experiences |
| 6 | Company insights: selection rate, average difficulty, top roles, question count | M2 Experiences |
| 7 | Question bank with topic, difficulty, company, role, tags, key-point answers | M3 Questions |
| 8 | Duplicate detection and merge (TF-IDF similarity ≥ 0.85) | M3 Questions |
| 9 | AI suggestion engine (TF-IDF + context signals) with explanations | M3 Questions |
| 10 | Timed mock interview sessions built from unseen questions, biased toward weak topics | M4 Practice |
| 11 | Automatic answer scoring with feedback (covered/missed key points) + self-rating | M4 Practice |
| 12 | Performance dashboard: averages, trend chart, topic breakdown, weak/strong topics, streak | M4 Practice |

## 4. Technology stack
| Layer | Choice | Reason |
|-------|--------|--------|
| Backend | Python 3.12, FastAPI | Typed, auto-generated OpenAPI docs, easy to test |
| Database | SQLite (dev) / any SQLAlchemy DB (prod) | Zero setup for demo; swappable via `DATABASE_URL` |
| ORM | SQLAlchemy 2.0 | Mature, typed mappings |
| Frontend | HTML + CSS + vanilla JS SPA | No build step; each module owns one JS file |
| Auth | JWT (PyJWT) + bcrypt | Stateless, industry standard |
| Testing | pytest + pytest-cov (branch coverage) | Required unit test + coverage report |
| CI/CD | Jenkins (Jenkinsfile) + GitHub Actions | Guidelines require Jenkins; Actions gives PR checks on GitHub |
| Quality | flake8, Bandit, pip-audit, SonarQube | Static analysis + security validation |
| Container | Docker, docker-compose | Reproducible deployment |
| Agile tracking | GitHub Issues + Projects board | User stories, backlog, sprints |

## 5. Novelty / differentiation
- Experiences **feed** the question bank automatically, so content grows without extra effort.
- **Duplicate merging** turns repetition into a signal ("asked 7×") instead of clutter.
- Suggestions are **explainable** ("asked at this company, targets a weak topic").
- The practice loop is **closed**: weak topics found by analytics change which questions the next mock interview picks.
- The AI engine runs **offline** with no API keys, and an LLM provider can be plugged in through the `SuggestionProvider` interface.
