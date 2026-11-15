# Final Demo & 15-Minute Presentation Plan

## Setup (before the slot)
```bash
docker compose up --build        # or: python -m scripts.seed && uvicorn app.main:app
```
Open three browser profiles logged in as student, moderator and admin (password `Demo@1234`). Keep the GitHub repo (Projects board, PRs, Actions), Jenkins and `htmlcov/index.html` in tabs.

## Running order
| Time | Speaker | Content | SDLC stage shown |
|------|---------|---------|------------------|
| 0:00–1:30 | Member 1 | Problem, solution, novelty (synopsis); team & module split | Requirements |
| 1:30–3:00 | Member 1 | Use-case diagram, measurable NFRs and security requirements from the SRS; register/login, role-based nav, wrong-password message; show a security test (token forgery) | Requirements, security validation |
| 3:00–5:30 | Member 2 | HLD module diagram; share an experience with 2 questions as student → it's pending → approve as moderator → appears in list; upvote; company insights page | Design, implementation |
| 5:30–8:00 | Member 3 | Add a reworded duplicate question → "merged", asked count 2. AI suggestions for "graph problems at Google" with reasons. Explain TF-IDF + weights from the LLD and show the recommender unit tests | Design (algorithms), unit tests |
| 8:00–10:30 | Member 4 | Start a mock interview, answer one well and one badly, see feedback; finish → key points revealed; dashboard (trend, weak topics); new session focuses on the weak topic | Implementation, system validation |
| 10:30–12:30 | Member 4 + 1 | Test report (91 tests, 99% coverage), RTM row walk-through, Jenkins/GitHub Actions run, Bandit result, Docker image | Testing, CI/CD |
| 12:30–13:30 | Member 2 | Agile: Projects board, user stories, PR with review comments, commit history per member | Agile process |
| 13:30–15:00 | All | Maintenance plan & roadmap; Q&A | Maintenance |

## Code walk-through each member must be ready for
- **M1:** `auth/service.py::authenticate`, `auth/deps.py::require_roles`, `security.py`.
- **M2:** `experiences/service.py::create` (calls M3), `get` visibility rule, `company_stats`.
- **M3:** `recommender.py::recommend` and `TfidfIndex`, `questions/service.py::create` duplicate check.
- **M4:** `practice/service.py::start` (weak topics → suggestions), `_expire_if_due`, `scorer.py::score_answer`.

## Differentiation to highlight
1. Experiences automatically grow the question bank.
2. Duplicates become a popularity signal instead of clutter.
3. Explainable AI suggestions, offline, pluggable for LLMs.
4. Closed practice loop: analytics change the next interview.
