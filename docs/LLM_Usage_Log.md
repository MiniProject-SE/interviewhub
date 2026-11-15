# LLM Usage Log

The guidelines allow LLMs but evaluate the prompts used and each member's understanding. Every member records significant prompts here and must be able to explain the resulting code line by line.

| Date | Member | Tool | Prompt (summary) | What was used | What we changed / verified |
|------|--------|------|------------------|---------------|----------------------------|
| 2026-11-15 | Team | Claude | Generate a modular FastAPI project for Project 18 with 4 modules, tests, CI/CD and SDLC docs | Initial code skeleton, tests, document drafts | Ran all tests; reviewed every module; fixed 4 defects found by tests (see Test Report §4) |
| | Member 1 | | | | |
| | Member 2 | | | | |
| | Member 3 | | | | |
| | Member 4 | | | | |

## Understanding checklist (each member, before the demo)
- [ ] I can draw my module's request flow: router → schema → service → model.
- [ ] I can explain every function in my module's `service.py` and why each check exists.
- [ ] I can explain my module's tests and which requirement each one verifies (RTM).
- [ ] I can change a business rule live (e.g. weak-topic threshold, duplicate threshold, password rule) and re-run tests.
- [ ] I can explain how my module calls / is called by other modules (HLD §4).

## Viva questions to prepare (by module)
**M1:** Why bcrypt and not SHA-256? What is inside a JWT and how is it verified? Why the same error for wrong email and wrong password? How does `require_roles` work as a FastAPI dependency?
**M2:** How is a company name normalised? Why do pending posts return 404 to other users instead of 403? How is selection rate computed and why exclude "pending"?
**M3:** Explain TF, IDF and cosine similarity with an example. Why are tags repeated in document terms? Why use text-only vectors for duplicate detection? What does each weight do?
**M4:** Walk through the session state machine. How is the auto score computed? Why combine with self-rating? How is the streak calculated? How do weak topics affect the next session?
