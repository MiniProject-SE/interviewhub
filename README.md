# InterviewHub

**Student's Interview Experience, Interview Question Bank and Practice Platform**
UE24CS341A Software Engineering · Jackfruit Mini-Project · Project ID 18

A crowdsourced platform where students share interview experiences organised by company and role, build a de-duplicated question bank, get AI-ranked question suggestions, and take timed mock interviews with instant scoring and progress tracking.

![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)

## Features
| Module | Owner | Highlights |
|--------|-------|-----------|
| **M1 Auth & Users** | Member 1 | JWT login, bcrypt, profiles, roles (student / moderator / admin), admin user management |
| **M2 Experiences** | Member 2 | Round-by-round experiences, filters, upvotes, moderation queue, company insights |
| **M3 Question Bank & AI** | Member 3 | Searchable bank, automatic duplicate merging, explainable TF-IDF suggestion engine |
| **M4 Mock Interview & Analytics** | Member 4 | Timed sessions, keyword-coverage scoring with feedback, dashboard with trend, weak topics, streak |

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m scripts.seed                                 # demo data
uvicorn app.main:app --reload
```
Open http://localhost:8000 (UI) and http://localhost:8000/docs (API docs).

Demo accounts (password `Demo@1234`): `student@interviewhub.dev`, `mod@interviewhub.dev`, `admin@interviewhub.dev`.

### With Docker
```bash
docker compose up --build
```

## Tests, coverage and quality
```bash
pytest                                  # unit + API tests with branch coverage (gate: 85%)
pytest --cov-report=html                # open htmlcov/index.html
flake8                # lint
bandit -r app -ll                       # security scan
```
Current status: **91 tests passing, 99.4% coverage.**

## CI/CD
- `Jenkinsfile`: install → lint → Bandit/pip-audit → pytest + coverage → SonarQube → Docker build → staging deploy.
- `.github/workflows/ci.yml`: same checks on every push and pull request, plus a container smoke test.
- `sonar-project.properties`: SonarQube configuration (run `docker compose --profile quality up sonarqube`).

## Project structure
```
app/core/              shared config, database, errors, text utils
app/modules/auth/      M1
app/modules/companies/ shared company catalogue (M3)
app/modules/experiences/ M2
app/modules/questions/ M3 (recommender.py = AI engine)
app/modules/practice/  M4 (scorer.py = answer scoring)
frontend/              SPA (one JS file per module)
tests/                 one test file per module
docs/                  SDLC documents
```

## Documentation
| Phase | Document |
|-------|----------|
| Synopsis | [docs/00_Synopsis.md](docs/00_Synopsis.md) |
| Requirements | [docs/01_SRS.md](docs/01_SRS.md) |
| Validation spec + traceability | [docs/02_Validation_Spec.md](docs/02_Validation_Spec.md) |
| Architecture (HLD) | [docs/03_HLD_Architecture.md](docs/03_HLD_Architecture.md) |
| Software design (LLD) | [docs/04_LLD_Software_Design.md](docs/04_LLD_Software_Design.md) |
| Agile plan & backlog | [docs/05_Agile_Plan.md](docs/05_Agile_Plan.md) |
| Unit test & coverage report | [docs/06_Test_Report.md](docs/06_Test_Report.md) |
| System validation & maintenance | [docs/07_System_Validation_and_Maintenance.md](docs/07_System_Validation_and_Maintenance.md) |
| Work division | [docs/08_Work_Division.md](docs/08_Work_Division.md) |
| Demo & presentation script | [docs/09_Demo_and_Presentation.md](docs/09_Demo_and_Presentation.md) |
| LLM usage log | [docs/LLM_Usage_Log.md](docs/LLM_Usage_Log.md) |
