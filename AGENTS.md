# Coding guidance — 지원장바구니

## Scope

Follow the user's current instructions, this file, and repository conventions. Use the code, public API contract and current test results to establish implemented behavior.

The original Streamlit/SQLite MVP is available at `v0.1-mvp` (`23f33e7bc8e51d3e26812faeb479aae7f83ee596`). Never rewrite this tag or old history. Develop changes on feature branches from main. Keep `app.py`, the collector, models and existing tests working alongside modules under `src/youth_policy/`. Keep deterministic business logic independent of UI, database and LLM providers.

## Product rules

- Situation cards are a starting point, not eligibility facts. Do not infer unemployment, income, distress, residence or age from a card.
- Support unknown, skip, answer correction and voluntary detail confirmation. Reuse answers and preserve them when detail is interrupted.
- Separate confirmed facts, preferences and unanswered questions. Preferences do not determine eligibility.
- Distinguish comparable conditions, clear mismatch, policy uncertainty and missing user input. No label guarantees application eligibility.
- Fixed choices and comparable conditions are handled by code. LLM output cannot override a clear exclusion or invent a policy.
- Policy amounts, periods, documents and contacts require official sources. Preserve policy IDs, URLs and verification times.
- The static demo uses synthetic policies and conditions. Its separate official-reference catalogue is not evidence for synthetic candidates.
- The intake API and demo do not call external models, persist user answers, submit applications or send messages. Browser print-to-PDF is a browser action.

## Repository and validation

- Public documentation describes current features, architecture, API contracts, setup and reproducible checks. Keep internal planning, meeting notes, role assignments and preparation records outside the public repository.
- Never commit secrets, raw snapshots, local databases or actual user answers. Use UTF-8 and portable `pathlib` paths.
- Every Python module starts with a short module docstring; public functions have type hints. Prefer small pure functions and immutable state updates.
- Preserve existing tests. Do not replace dependencies with test shims.
- Use the repository virtual environment explicitly: Windows `.\\.venv\\Scripts\\python.exe`, Linux `.venv/bin/python`.
- Run relevant tests, full pytest when dependencies are available, and compileall for Python changes. Report blocked or skipped checks; do not present historical totals as current results.
- Describe intended files and purpose before edits. Report changed behavior and executed checks afterward.
- Keep public documentation and links consistent with the current code. Do not present unimplemented components or evaluation targets as working features.
