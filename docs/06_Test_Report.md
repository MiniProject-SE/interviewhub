# Unit Test & Coverage Report — InterviewHub

**Command:** `pytest` (configured in `pytest.ini` with `--cov=app --cov-branch`)
**Environment:** Python 3.12/3.13, SQLite in-memory per test, Linux
**Result:** **91 tests, 91 passed, 0 failed, 0 skipped**
**Coverage:** **99.4% combined statement + branch coverage** (1,242 statements, 208 branches; 6 statements and 3 branch paths not covered). CI gate: 85%.

Regenerate the HTML report with `pytest --cov-report=html` and open `htmlcov/index.html`. Jenkins archives `htmlcov/`, `coverage.xml` and `reports/junit.xml` on every build.

## 1. Results by module
| Module | Owner | Test file(s) | Tests | Result |
|--------|-------|--------------|-------|--------|
| M1 Auth & Users | Member 1 | `test_auth.py` | 22 | All pass |
| M2 Experiences & Companies | Member 2 | `test_experiences.py` | 19 | All pass |
| M3 Question Bank & AI | Member 3 | `test_questions.py`, `test_recommender.py` | 24 | All pass |
| M4 Mock Interview & Analytics | Member 4 | `test_practice.py` | 26 | All pass |
| **Total** | | | **91** | **All pass** |

(Parametrised tests count once per parameter set.)

## 2. Coverage by file
| File | Stmts | Miss | Branches | Partial | Cover |
|------|------:|-----:|---------:|--------:|------:|
| core/config.py | 15 | 0 | 0 | 0 | 100% |
| core/database.py | 23 | 4 | 2 | 1 | 80% |
| core/errors.py | 15 | 0 | 0 | 0 | 100% |
| core/text.py | 11 | 0 | 4 | 0 | 100% |
| auth/deps.py | 29 | 2 | 8 | 0 | 95% |
| auth/models.py, router.py, schemas.py, security.py, service.py | 198 | 0 | 24 | 0 | 100% |
| companies/models.py, service.py | 40 | 0 | 6 | 0 | 100% |
| experiences/models.py, router.py, schemas.py, service.py | 274 | 0 | 34 | 0 | 100% |
| questions/models.py, router.py, schemas.py, service.py | 206 | 0 | 36 | 0 | 100% |
| questions/recommender.py | 116 | 0 | 30 | 0 | 100% |
| practice/models.py, router.py, schemas.py | 130 | 0 | 0 | 0 | 100% |
| practice/scorer.py | 66 | 0 | 34 | 1 | 99% |
| practice/service.py | 119 | 0 | 30 | 1 | 99% |
| **Total** | **1242** | **6** | **208** | **3** | **99.4%** |

### Uncovered code (justified)
| Location | Reason |
|----------|--------|
| `core/database.py` 25–29 (`get_db`) | Production session generator; tests replace it with an in-memory override. Exercised by the running app and system tests. |
| `core/database.py` 14→16 | Non-SQLite engine branch (PostgreSQL); covered in deployment smoke test. |
| `auth/deps.py` 39–40 | `get_optional_user` invalid-token fallback; low risk, scheduled for release v1.1. |
| `scorer.py` 42→39, `service.py` 173→176 | Loop-exit partial branches with no behavioural difference. |

## 3. Static analysis & security scan
| Tool | Result |
|------|--------|
| flake8 (max line 130) | 0 issues |
| Bandit `-r app -ll` | No medium or high severity issues |
| pip-audit | Run in CI on every build (non-blocking, reviewed weekly) |
| SonarQube | `sonar-project.properties` reads `coverage.xml` and `reports/junit.xml` |

## 4. Defects found during testing (and fixed)
| ID | Found by | Defect | Fix |
|----|----------|--------|-----|
| BUG-1 | `test_duplicate_is_merged` | Duplicate detection compared plain question text with tag-boosted vectors, so an identical question scored only 0.84 and was not merged. | Added `text_only` mode to `TfidfIndex` for duplicate checks. |
| BUG-2 | `test_update_permissions` | `PATCH /api/questions/{id}` with `"difficulty": null` caused a database NOT NULL error (500). | Explicit nulls on required fields are now ignored. |
| BUG-3 | `test_score_middle_band_and_stemming` | Stemmer turned "process" into "proces", so answers saying "processes" missed the keyword. | Words ending in "ss" are kept; "sses" → "ss". |
| BUG-4 | Manual review | "thread" and "threads" were both chosen as keywords, double-counting one idea. | Keywords de-duplicated by stem. |

## 5. Performance check (NFR-2)
`test_nfr2_ranking_1000_questions_under_200ms` ranks 1,000 synthetic questions; measured ~15 ms on the dev machine (limit 200 ms).
