# Contributing

1. Pick an issue from the GitHub Projects board and assign yourself.
2. Branch from `main`: `git checkout -b feature/<module>-<short-name>`.
3. Keep changes inside your module (`app/modules/<module>/`, `frontend/js/<module>.js`, `tests/test_<module>.py`). Shared files (`app/main.py`, `app/core/database.py`, `frontend/index.html`, `frontend/js/app.js`) should only gain one registration line per module.
4. Before pushing run:
   ```bash
   flake8 && bandit -r app -ll && pytest
   ```
5. Commit with conventional messages: `feat(questions): add duplicate merge`, `test(practice): cover expiry`, `docs: update RTM`.
6. Open a PR using the template, link the story (`Closes #12`), request review from the next member in the review cycle (M1→M2→M3→M4→M1).
7. Merge only when CI is green and one approval is given. Do not push directly to `main`.

## Changing a cross-module interface
Interfaces listed in `docs/03_HLD_Architecture.md` §4 are frozen. To change one, open an issue, tag both owners, and update the HLD/LLD in the same PR.
