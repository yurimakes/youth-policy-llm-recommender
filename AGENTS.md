# AGENTS.md

## 1. Purpose and authority

This repository contains the implementation of **청년 맞춤 정책 추천 및 신청 지원 웹서비스** for the P-커리어캐치Ⅳ project.

The administrative source document is `p커리어캐치Ⅳ_최유리_제출본.docx`. The first three daily reports were written on the assumption that design and development work had been performed, but the actual codebase starts from this repository. Do not assume that code, data, tests, database tables, or deployment artifacts already exist unless they are present in the repository.

When instructions conflict, follow this order:

1. The user's latest explicit instruction
2. `PROJECT_SPEC.md`
3. This file
4. Existing repository conventions

Do not silently change the agreed project scope.

## 2. Working style with the user

The user wants development to proceed **one verified step at a time**.

- Present only the immediate task or proposed change.
- Do not provide the entire remaining roadmap unless the user asks for it.
- Before modifying files, briefly state which files will change and why.
- Wait for approval when a change introduces a new dependency, changes architecture, expands scope, or removes existing work.
- After each task, report changed files, commands executed, test results, and any unresolved issue.
- Do not advance to the next task until the current task has been verified or the user explicitly asks to continue.

## 3. MVP technology decisions

Use the following stack for the MVP:

- Python 3.12
- Streamlit for the web UI and application entry point
- Requests for public API calls
- Pandas for tabular processing
- SQLite for structured, local policy data
- FAISS for vector similarity search
- OpenAI API for embeddings and grounded explanations
- Default embedding model: `text-embedding-3-small`
- pytest for automated tests
- Streamlit Community Cloud for deployment

The MVP is a single Streamlit application. Do not introduce FastAPI, MySQL, PostgreSQL, ChromaDB, a separate frontend framework, or a separate backend service without explicit approval.

A small supporting dependency may be proposed only when it is clearly necessary. Explain the reason before adding it.

## 4. MVP scope boundaries

The initial MVP excludes:

- FastAPI server separation
- MySQL or PostgreSQL
- ChromaDB
- Selenium-based large-scale crawling
- Simultaneous integration of multiple policy providers
- User accounts, login, and personal data persistence
- Policy application submission or automation
- Payment functionality
- Administrator dashboard
- Native mobile application

These may be documented as future extensions, not implemented as part of the initial MVP.

## 5. Required application flow

Keep the core flow deterministic and traceable:

1. Collect user profile conditions and an optional natural-language request.
2. Apply Python rule-based filtering to structured policy fields.
3. Retain uncertain cases as `UNKNOWN` rather than inventing or over-interpreting conditions.
4. Rank remaining candidates with FAISS semantic similarity.
5. Pass only retrieved official policy data to the OpenAI API.
6. Generate a grounded explanation, not a new eligibility decision.
7. Display results, uncertainty, official source links, and verification dates in Streamlit.

The LLM must not independently choose policies from outside the retrieved candidate set.

## 6. Policy recommendation safety rules

The service does not make a final legal or administrative eligibility determination.

Display a notice with this meaning in the UI:

> 지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.

The implementation must follow these rules:

- Never invent eligibility rules, benefit amounts, dates, application methods, required documents, or contact details.
- Treat missing or ambiguous data as unknown.
- Show unknown items under “확인이 필요한 조건”.
- Exclude closed policies from default recommendations when closure can be determined reliably.
- Do not exclude a policy solely because a condition is missing or unparseable.
- Preserve and display the official source URL.
- Preserve and display `last_verified_at` when available.
- Clearly distinguish official source data from generated explanations.
- Keep LLM prompts limited to the retrieved policy context.
- Do not use wording such as “신청 가능합니다” or “자격이 확정되었습니다”.

## 7. Primary data source and collection rules

Use the **온통청년 청년정책 API** as the primary data source for the MVP.

- Preserve raw API responses as timestamped snapshots.
- Keep raw and processed data in separate locations.
- Make data cleaning reproducible through scripts or functions.
- Record source name, source URL, and verification time.
- Use official sources only when manually supplementing missing application documents or procedures.
- Do not add scraped data from other providers until the primary pipeline works end to end.
- Treat 복지로 and 서울시 youth-policy data as optional future extensions.
- Do not use Selenium in the MVP unless the user explicitly changes the scope.

Runtime operation on Streamlit Community Cloud must not depend on persistent local writes. SQLite and FAISS artifacts should be treated as reproducible, read-oriented build artifacts at runtime.

## 8. Canonical policy fields

Design the processed dataset around these canonical fields:

- `policy_id`
- `policy_name`
- `category`
- `summary`
- `region_code`
- `region_name`
- `age_min`
- `age_max`
- `income_condition`
- `employment_status`
- `education_status`
- `application_start`
- `application_end`
- `application_status`
- `eligibility_text`
- `benefit_text`
- `application_method`
- `required_documents`
- `contact`
- `source_name`
- `source_url`
- `last_verified_at`
- `embedding_text`

If the source API does not provide a field, do not fabricate it. Document the mapping, derivation, or null-handling rule. Preserve important original fields when they are needed for traceability.

## 9. Filtering semantics

Implement eligibility checks as a tri-state result:

- `MATCH`: available structured data supports the user's condition.
- `NO_MATCH`: available structured data clearly contradicts the user's condition.
- `UNKNOWN`: data is missing, ambiguous, or cannot be parsed safely.

Rules:

- Age, region, and reliably derived application status may be used as hard filters.
- Income, employment, and education conditions must not be treated as hard exclusions when the source is free text or ambiguous.
- Exclude only clear `NO_MATCH` cases for required conditions.
- Keep `UNKNOWN` cases and expose them as items requiring confirmation.
- Record matched, unmatched, and unknown reasons so the UI and tests can inspect them.

## 10. LLM and embedding rules

- Read model names from environment variables; do not hardcode them in business logic.
- Default environment variable names:
  - `OPENAI_API_KEY`
  - `OPENAI_CHAT_MODEL`
  - `OPENAI_EMBEDDING_MODEL`
- Default embedding model is `text-embedding-3-small` unless the user changes it.
- The chat model is configurable and must not be described as permanently fixed in documentation.
- Embeddings should be generated from a documented `embedding_text` construction rule.
- Keep a stable mapping between each FAISS vector position and `policy_id`.
- Do not call external APIs in unit tests; use mocks or fixtures.
- Validate generated output before displaying it when a structured response format is used.
- On an LLM failure, preserve the retrieved policy results and show a clear explanation-generation error instead of hiding all results.

## 11. Secret and configuration management

Never commit or print secrets.

- Store local secrets in `.env` or `.streamlit/secrets.toml`.
- Add both secret files to `.gitignore`.
- Provide `.env.example` with variable names only.
- Do not place real API keys in source code, tests, notebooks, screenshots, documentation, logs, or Git history.
- Read configuration through a central configuration module rather than scattered `os.getenv` calls.
- Fail with a helpful message when a required secret is missing.

## 12. Data and repository hygiene

- Use UTF-8.
- Use `pathlib.Path` for filesystem paths.
- Avoid absolute paths tied to one computer.
- Do not overwrite raw source snapshots.
- Use ISO-style dates (`YYYY-MM-DD`) in processed data where possible.
- Keep generated indexes and large data files out of Git unless their inclusion is explicitly approved and reasonable in size.
- Do not commit `.venv`, cache files, secret files, or local database journals.
- Preserve reproducibility: another developer should be able to rebuild processed data and indexes from documented inputs.

## 13. Code quality rules

- Use clear English names for modules, functions, variables, and classes.
- Korean is appropriate for user-facing UI text and project documentation.
- Prefer small, focused functions and modules.
- Add type hints to public functions and non-trivial internal functions.
- Add concise docstrings where behavior is not obvious.
- Avoid broad `except Exception` unless re-raising or converting it into a clear domain error.
- Use logging for operational messages; avoid debug `print` statements in committed code.
- Keep business logic outside Streamlit UI callbacks where practical.
- Separate data collection, normalization, filtering, retrieval, LLM explanation, and UI responsibilities.
- Avoid unnecessary abstraction and premature optimization.
- Do not duplicate business rules across UI and backend modules.

## 14. Testing and verification

Use pytest. Tests should cover at least:

- Source-to-canonical field mapping
- Null and malformed-value handling
- Date and application-status derivation
- Tri-state condition filtering
- Closed-policy exclusion
- Retention of unknown conditions
- FAISS index-to-`policy_id` mapping
- Prompt grounding and output validation where applicable
- Streamlit-facing service behavior through testable non-UI functions

Default verification commands, once the relevant files exist:

```bash
python -m pytest
python -m compileall app.py src
```

For manual application verification:

```bash
python -m streamlit run app.py
```

Run the smallest relevant test set during development and the full test suite before declaring a milestone complete. Never claim a test passed unless it was actually executed.

## 15. Documentation rules

Keep these documents consistent:

- `PROJECT_SPEC.md`: product requirements and architectural decisions
- `TASKS.md`: current implementation status and the next approved task
- `README.md`: public project introduction and verified setup instructions
- `AGENTS.md`: persistent instructions for coding agents

Do not document planned functionality as completed. Update README commands only after verifying them locally. Record important architecture changes in the specification before implementation.

## 16. Change discipline

Before coding:

- Read `AGENTS.md`, `PROJECT_SPEC.md`, and relevant existing files.
- State the goal, proposed files, and verification method.
- Ask before changing architecture or scope.

After coding:

- Summarize what changed.
- List exact files changed.
- Report commands and test results.
- State limitations or follow-up issues honestly.
- Do not create fake data, fake test outcomes, fake deployment URLs, or fabricated report evidence.

## 17. Definition of done for an individual task

A task is complete only when:

- The requested behavior is implemented within the approved scope.
- Relevant tests are added or updated.
- Relevant tests pass.
- No secret or machine-specific path is introduced.
- Documentation is updated when behavior or setup changed.
- The user receives a concise verification summary and chooses whether to continue.
