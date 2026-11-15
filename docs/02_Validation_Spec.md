# Validation Specification & Requirements Traceability — InterviewHub

Covers the three validation-spec deliverables: initial planning (Requirements phase), update after Architecture/Design, and update after Implementation.

## 1. Validation strategy
| Level | Technique | Tool | Owner |
|-------|-----------|------|-------|
| Unit (white box) | Pure-function tests for scorer, recommender, security, slug, streak; branch coverage | pytest, pytest-cov | Each module owner |
| Integration / API (black box) | HTTP tests through FastAPI TestClient with isolated in-memory DB per test | pytest + httpx | Each module owner |
| Security | Auth/authorisation negative tests, token tampering/expiry, input validation, Bandit SAST, pip-audit, header checks | pytest, Bandit, pip-audit | M1 lead, all review |
| System / usage-driven | End-to-end scenarios through the UI (see §6) | Browser, Playwright smoke | Whole team |
| Static quality | Lint + SonarQube quality gate | flake8, SonarQube | CI |
| Regression | Full suite on every push/PR | Jenkins, GitHub Actions | CI |

**Entry criteria:** feature branch builds, PR opened with linked user story.
**Exit criteria:** all tests pass, overall branch coverage ≥ 85% (NFR-3), Bandit reports no medium/high issues, one reviewer approval.

## 2. Test environment
Python 3.12, SQLite in-memory (`StaticPool`) per test for isolation; Docker image for system tests.

## 3. Security validation & penetration test plan
| ID | Attack / check | Expected result | Test |
|----|----------------|-----------------|------|
| PT-1 | Access protected endpoints without token / with garbage token | 401 | `test_protected_route_requires_token` |
| PT-2 | Expired JWT | 401 | `test_expired_token_rejected` |
| PT-3 | JWT signed with attacker key (forgery) | Rejected | `test_tampered_token_rejected` |
| PT-4 | Token for deleted / deactivated user | 401 | `test_token_for_deleted_user_rejected`, `test_deactivated_user_cannot_login` |
| PT-5 | User enumeration via login messages | Identical response | `test_login_failure_same_message` |
| PT-6 | Privilege escalation: student calls admin/moderator endpoints | 403 | `test_admin_user_management`, `test_moderation_flow`, `test_delete_only_moderators` |
| PT-7 | IDOR: read another user's practice session | 404 | `test_answer_wrong_item_or_other_user` |
| PT-8 | IDOR: view another user's pending experience | 404 | `test_pending_visible_to_author_not_others` |
| PT-9 | Weak password / malformed email / oversize input | 422 | `test_weak_passwords_rejected`, `test_invalid_email_and_short_name_rejected` |
| PT-10 | SQL injection in search params | Treated as literal text (ORM binds) | Code review + manual `q=' OR 1=1 --` |
| PT-11 | Stored XSS in experience summary | Rendered escaped | `esc()` in `frontend/js/api.js`, manual check |
| PT-12 | Clickjacking / MIME sniffing | Headers present | `test_health_and_security_headers` |
| PT-13 | Vulnerable code patterns / dependencies | No medium+ findings | Bandit + pip-audit CI stage |

## 4. Test case catalogue (summary)
Full test code is in `tests/`. Representative cases:

| TC ID | Description | Type | Test function |
|-------|-------------|------|---------------|
| TC-1.1 | First user becomes admin; password not echoed | API | `test_register_first_user_is_admin` |
| TC-1.2 | Email normalised and unique | API | `test_second_user_is_student`, `test_duplicate_email_rejected` |
| TC-1.3 | Login + `/users/me` | API | `test_login_success_and_me` |
| TC-1.4 | Profile update | API | `test_update_profile` |
| TC-1.5 | Password change | API | `test_change_password` |
| TC-1.6 | Admin role management and self-protection | API | `test_admin_user_management`, `test_admin_cannot_demote_or_disable_self` |
| TC-2.1 | Student post is pending, questions fed to bank | API | `test_student_post_goes_to_moderation` |
| TC-2.2 | Validation of experience fields (5 cases) | API | `test_validation[...]` |
| TC-2.3 | Moderation approve / reject | API | `test_moderation_flow`, `test_reject` |
| TC-2.4 | Browse filters, sort, pagination | API | `test_browse_filters_and_sort` |
| TC-2.5 | Vote toggle, no self-vote | API | `test_vote_toggle_and_self_vote` |
| TC-2.6 | Edit/delete permissions | API | `test_update_and_delete_permissions` |
| TC-2.7 | Company statistics incl. empty company | API | `test_company_stats`, `test_company_stats_empty_company` |
| TC-2.8 | Company slug normalisation | Unit | `test_company_slug_and_dedupe` |
| TC-3.1 | Question create + validation + tag cleaning | API | `test_create_requires_login_and_validates` |
| TC-3.2 | Duplicate merged / different not merged | API | `test_duplicate_is_merged`, `test_different_question_not_merged` |
| TC-3.3 | Search filters & pagination | API | `test_search_filters` |
| TC-3.4 | Suggestion ranking, topic filter, limit validation | API | `test_suggest_endpoint` |
| TC-3.5 | TF-IDF similarity / IDF / cosine edges | Unit | `test_index_similarity_prefers_matching_doc`, `test_cosine_edge_cases` |
| TC-3.6 | Signal boosts (company, role, weak topic) | Unit | `test_recommend_*` |
| TC-3.7 | Score bounds and ordering; weights sum to 1 | Unit | `test_scores_are_bounded_and_sorted`, `test_weights_sum_to_one` |
| TC-3.8 | Provider is pluggable | Unit | `test_provider_is_pluggable` |
| TC-4.1 | Keyword extraction, stemming, scoring bands | Unit | `test_extract_keywords_*`, `test_score_*` |
| TC-4.2 | Start session, model answers hidden | API | `test_start_session` |
| TC-4.3 | Answer, finish, total score, key points revealed, closed session rejects | API | `test_answer_and_finish` |
| TC-4.4 | Expiry after deadline | API | `test_session_expires` |
| TC-4.5 | Unseen-first selection then repeats | API | `test_prefers_unseen_questions_then_allows_repeats` |
| TC-4.6 | Analytics: weak/strong, trend, improvement, minutes, streak | API | `test_analytics_weak_strong_trend` |
| TC-4.7 | Streak algorithm (6 boundary cases) | Unit | `test_streak_days[...]` |

## 5. Non-functional validation plan
| NFR | Method | Pass criterion |
|-----|--------|----------------|
| NFR-1 | Load 1,000 questions via seed script; run Locust with 20 users for 2 min against `/api/questions` and `/api/experiences` | p95 < 300 ms |
| NFR-2 | Time `recommend()` over 1,000 synthetic docs | < 200 ms |
| NFR-3 | CI coverage gate (`fail_under = 85`) | Build fails below threshold |
| NFR-4 | Walkthrough with 3 classmates | Session started within 3 clicks |
| NFR-6 | `docker compose up` on clean machine | App reachable on :8000 |

## 6. System validation scenarios (usage-driven, black box)
| SV ID | Scenario | Steps | Expected |
|-------|----------|-------|----------|
| SV-1 | New student onboarding | Register → login → profile → dashboard | Empty dashboard with "start a mock interview" link |
| SV-2 | Share and publish | Student posts experience with 2 questions → moderator approves | Experience visible in list; 2 questions in bank linked to it |
| SV-3 | Duplicate contribution | Another student adds the same question with different wording | "Merged" toast; times_asked = 2 |
| SV-4 | Company prep | Open company insights → "Practice for Company" | Session questions from that company first |
| SV-5 | Practice loop | Complete a poor session on DBMS → start new session with weak focus | Dashboard lists DBMS as weak; next session boosts DBMS |
| SV-6 | Timer expiry | Start 5-minute session, wait | Session shows *expired*, answers locked |
| SV-7 | Abuse | Student tries moderation URL | 403 / hidden nav |

## 7. Requirements Traceability Matrix (RTM)
| Requirement | Design element (LLD) | Code | Test cases | Status |
|-------------|---------------------|------|-----------|--------|
| FR-1.1 | `auth.service.register`, `RegisterRequest` | `app/modules/auth/` | TC-1.1, TC-1.2, PT-9 | Pass |
| FR-1.2 | `auth.security.create_access_token` | `auth/security.py` | TC-1.3, PT-2, PT-3 | Pass |
| FR-1.3 | `register()` first-user rule | `auth/service.py` | TC-1.1 | Pass |
| FR-1.4 | `update_profile` | `auth/service.py` | TC-1.4 | Pass |
| FR-1.5 | `change_password` | `auth/service.py` | TC-1.5 | Pass |
| FR-1.6 | `set_role`, `set_active`, `require_roles` | `auth/service.py`, `deps.py` | TC-1.6, PT-6 | Pass |
| FR-1.7 | `authenticate`, `get_current_user` | `auth/service.py`, `deps.py` | PT-4 | Pass |
| FR-2.1 | `experiences.service.create` | `app/modules/experiences/` | TC-2.1 | Pass |
| FR-2.2 | `ExperienceCreate` validators | `experiences/schemas.py` | TC-2.2 | Pass |
| FR-2.3 | status + `get()` visibility rule | `experiences/service.py` | TC-2.1, TC-2.3, PT-8 | Pass |
| FR-2.4 | `browse()` | `experiences/service.py` | TC-2.4 | Pass |
| FR-2.5 | `toggle_vote`, `ExperienceVote` unique | `experiences/` | TC-2.5 | Pass |
| FR-2.6 | `update`, `delete` | `experiences/service.py` | TC-2.6 | Pass |
| FR-2.7 | `company_stats` | `experiences/service.py` | TC-2.7 | Pass |
| FR-2.8 | `companies.slugify`, `get_or_create` | `app/modules/companies/` | TC-2.8 | Pass |
| FR-2.9 | `create()` → `questions.service.create` | `experiences/service.py` | TC-2.1 | Pass |
| FR-3.1 | `QuestionCreate`, `questions.service.create` | `app/modules/questions/` | TC-3.1 | Pass |
| FR-3.2 | `questions.service.search` | `questions/service.py` | TC-3.3 | Pass |
| FR-3.3 | `TfidfIndex(text_only=True).most_similar`, `DUPLICATE_THRESHOLD` | `questions/recommender.py` | TC-3.2 | Pass |
| FR-3.4 | `recommend`, `WEIGHTS`, `_explain` | `questions/recommender.py` | TC-3.4, TC-3.6, TC-3.7 | Pass |
| FR-3.5 | topic hard filter in `recommend` | `questions/recommender.py` | TC-3.4 | Pass |
| FR-3.6 | `update`, `delete` | `questions/service.py` | `test_update_permissions`, `test_delete_only_moderators` | Pass |
| FR-3.7 | `SuggestionProvider` protocol | `questions/recommender.py` | TC-3.8 | Pass |
| FR-4.1 | `practice.service.start` | `app/modules/practice/` | TC-4.2, TC-4.5 | Pass |
| FR-4.2 | `to_out()` hides `model_answer` | `practice/service.py` | TC-4.2 | Pass |
| FR-4.3 | `scorer.score_answer`, `combine` | `practice/scorer.py` | TC-4.1, TC-4.3 | Pass |
| FR-4.4 | `finish`, `_finalise` | `practice/service.py` | TC-4.3 | Pass |
| FR-4.5 | `_expire_if_due` | `practice/service.py` | TC-4.4 | Pass |
| FR-4.6 | `analytics`, `streak_days` | `practice/service.py` | TC-4.6, TC-4.7 | Pass |
| FR-4.7 | `history`, ownership check in `get` | `practice/service.py` | `test_history`, PT-7 | Pass |
| SR-1…SR-10 | see §3 | various | PT-1…PT-13 | Pass |
| NFR-3 | `.coveragerc fail_under=85` | CI | Coverage report | Pass (99.4%) |
