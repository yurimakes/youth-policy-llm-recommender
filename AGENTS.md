# Coding guidance — 지원장바구니

## Authority and scope

Follow the user's current instructions, `PROJECT_SPEC.md`, this file, then repository conventions. The current product is **지원장바구니: 청년정책 AI 에이전트**. Read `PROJECT_STATUS.md` before claiming a feature is implemented.

The original Streamlit/SQLite MVP is preserved by `v0.1-mvp` at `23f33e7bc8e51d3e26812faeb479aae7f83ee596`. Never rewrite this tag or old history. Develop follow-up work on feature branches from the merged main branch; record the active branch in PROJECT_STATUS. Keep the old collector, models, tests and `app.py` working while developing reusable modules under `src/youth_policy/`.

The latest plan authorizes React/TypeScript, FastAPI, PostgreSQL and later LangGraph and retrieval work. They are planned components, not proof of working integrations. Introduce each component with an explicit purpose and relevant verification. Keep deterministic business logic independent of UI, database and LLM providers.

## Team ownership

The user's approved `청년정책_화면흐름보드_v1.zip` supersedes the initial three-view scope (2026-10-08). Implement situation, interest, basic questions, directions, optional detail, updated results, a memory-only basket, preparation and deterministic consultation drafts under `demo/`. Keep the lightweight HTML/CSS/JavaScript demo served by local FastAPI. React/TypeScript remains the later frontend direction.

The user authorized a public demo with mock data. The static deployment explicitly labels synthetic policies/conditions; it is not a hosted Python API or a real eligibility service. Keep `mock.mjs` independent from the real API's rules and fields. Actual policy references are a separate dated catalogue, not evidence for the synthetic candidates. Never infer official requirements or current availability from mock data. No external model calls, user-answer persistence, automatic submission or messaging. Print-to-PDF is a browser action, not an AI document service. Preserve the approved blue/gray visual design.

## Product rules

- Situation/interest cards are a valid starting point without a stated goal. Support unknown and skip as normal answers.
- A situation card is not an eligibility fact. Never derive unemployment, income, distress or residence from a card.
- Do not assume Seoul residence or age 19–34 from the recruitment target.
- Offer detailed questions after an explicit interest action, and enter only on the user's choice. Keep the basic route available.
- Reuse answers; allow correction, unknown, skip, interruption and return. Ask only for missing information useful to current candidates or next actions.
- Separate confirmed facts, preferences and unanswered questions. Preferences never determine eligibility.
- Distinguish confirmed comparable conditions, clear mismatch, policy/agency uncertainty and missing user input. No label establishes final application eligibility.
- Code handles fixed choices and comparable conditions; LLM output never overrides a clear exclusion or invents a policy.
- Only official policy fields support amounts, periods, documents and contact details. Preserve policy IDs, URLs and verification times.
- No automatic application submission, messages, login or personal-data persistence in this milestone. Do not send free text to an external model without an approved processing design.

## Repository and validation

- Never commit secrets, raw snapshots, local databases, actual user answers or audit artifacts. Use UTF-8 and portable `pathlib` paths.
- Keep configuration central; model/API choices and data retention remain open decisions.
- Every Python module starts with a short module docstring; public functions have type hints. Prefer small pure functions and immutable state updates.
- Keep existing pytest tests. New standard-library-only tests may use unittest (pytest also discovers them). Do not replace dependencies with test shims.
- Use the repository virtual environment explicitly: Windows `.\.venv\Scripts\python.exe`, Linux `.venv/bin/python`.
- Run relevant tests, full pytest when dependencies are available, and compileall. If a dependency or network restriction prevents a check, report the limitation and leave it pending; never claim historical test totals as current results.
- Describe intended files and purpose before edits; report changed behavior, executed checks and remaining work afterward. The user's authorization to continue development applies to the current plan; do not repeatedly ask to reconfirm it.
- Keep README, PROJECT_SPEC, PROJECT_STATUS and TASKS consistent. User testing, deployment, RAG, model calls and evaluation targets remain planned until actually verified.
