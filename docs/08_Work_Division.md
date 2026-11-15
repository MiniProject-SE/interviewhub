# Division of Work

Each member owns **one complete functionality end to end** (model → service → API → UI → tests → documentation), as the guidelines require. Commits for each module are pushed by its owner from their own GitHub account on their own feature branch, and merged through a reviewed pull request.

Replace "Member N" with names and SRNs.

| | Member 1 | Member 2 | Member 3 | Member 4 |
|---|---|---|---|---|
| **Name / SRN** | | | | |
| **Functionality** | Authentication, users & roles | Interview experiences & companies | Question bank & AI suggestions | Mock interview & performance tracking |
| **Backend** | `app/core/*`, `app/main.py`, `app/modules/auth/*` | `app/modules/experiences/*` | `app/modules/questions/*` (incl. `recommender.py`), `app/modules/companies/*` | `app/modules/practice/*` (incl. `scorer.py`) |
| **Frontend** | `index.html`, `styles.css`, `api.js`, `auth.js`, `app.js` | `experiences.js` | `questions.js` | `practice.js` |
| **Tests** | `conftest.py`, `test_auth.py` (22) | `test_experiences.py` (19) | `test_questions.py`, `test_recommender.py` (24) | `test_practice.py` (26) |
| **DevOps** | Jenkinsfile, pytest/coverage/flake8 config, requirements | Dockerfile, docker-compose, seed data | SonarQube config | GitHub Actions, PR/issue templates |
| **Documents** | SRS, README, Contributing, Work division, LLM log | Synopsis, HLD architecture, Agile plan | LLD software design | Validation spec + RTM, Test report, System validation & maintenance, Demo script |
| **Sprint 1 part** | 1A: US-1.1, 1.2, 1.3, 0.1 | 1B: US-2.1, 2.2, 2.6 | 1C: US-3.1, 3.2, 3.3 | 1D: US-4.1, 4.3 |
| **Sprint 2 part** | 2A: US-1.4, 1.5 | 2B: US-2.3, 2.4, 2.5, 0.2 | 2C: US-3.4, 3.5 | 2D: US-4.2, 4.4, 4.5 |
| **Branches** | `feature/s1-m1-auth`, `feature/s2-m1-auth` | `feature/s1-m2-experiences`, `feature/s2-m2-experiences` | `feature/s1-m3-question-bank`, `feature/s2-m3-question-bank` | `feature/s1-m4-mock-interview`, `feature/s2-m4-mock-interview` |
| **Reviews PRs of** | Member 4 | Member 1 | Member 2 | Member 3 |
| **Demo segment** | Login, roles, security tests, CI pipeline | Share → moderate → browse → company insights | Duplicate merge, AI suggestions & ranking math | Mock interview, scoring, dashboard |

## Size of each contribution (non-blank lines)
| Member | Backend | Tests | Frontend | DevOps/config | Docs |
|--------|--------:|------:|---------:|--------------:|-----:|
| 1 | ~380 | ~180 | ~190 | ~110 | ~210 |
| 2 | ~320 | ~110 | ~130 | ~240 | ~240 |
| 3 | ~450 | ~140 | ~100 | ~10 | ~230 |
| 4 | ~380 | ~130 | ~140 | ~40 | ~260 |

## Integration points (who depends on whom)
- Everyone uses Member 1's `get_current_user` / `require_roles`.
- Member 2 calls Member 3's `questions.service.create()` to add asked questions to the bank, and Member 3's company catalogue.
- Member 4 calls Member 3's `questions.service.suggest()` to choose interview questions.
- Shared registration files (`main.py`, `database.py`, `index.html`, `app.js`) get one line per module from each owner's PR.

**Merge order:** one PR per member per sprint (8 PRs). In each sprint: M1 → M3 → M2 → M4, because each part builds on the previous one.
