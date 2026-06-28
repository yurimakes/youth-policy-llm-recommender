# PROJECT_SPEC.md

## 1. Document status

- Project: **청년 맞춤 정책 추천 및 신청 지원 웹서비스**
- Program: P-커리어캐치Ⅳ
- Administrative baseline: `p커리어캐치Ⅳ_최유리_제출본.docx`
- Development baseline: new implementation beginning in `C:\choiyuri\school\gachon_summer\career-catch-4`
- Primary language: Korean UI and documentation, English code identifiers
- Status: MVP specification before implementation

The first three daily reports were prepared on the assumption that planning and development activities had been completed. They are not evidence that a working codebase already exists. Actual implementation, tests, data artifacts, and deployment must be created and verified from this repository.

## 2. Project summary

Government and local-government youth policies are distributed across many platforms, use different terminology, and often contain complex eligibility and application requirements. A young person may need to compare age, residence, income, employment, education, application dates, supporting documents, and regional rules before deciding whether a policy is relevant.

This project will build a web prototype that:

1. Collects a user's basic conditions and natural-language need.
2. Filters official youth-policy data using deterministic rules.
3. Ranks relevant candidates with semantic search.
4. Uses a large language model only to explain retrieved official information.
5. Shows application guidance, uncertainty, official sources, and verification dates.

The service is an information and recommendation aid, not an eligibility-certification or application-submission system.

## 3. Problem statement

Current policy-search experiences have several limitations:

- Policy information is spread across government and local platforms.
- Eligibility conditions are difficult to compare quickly.
- Keyword search does not fully reflect a user's situation or intent.
- Application procedures and required documents are often buried in long notices.
- Users may mistake generated summaries for official eligibility decisions.
- Policy dates and details change, creating a freshness and trust problem.

The MVP addresses these problems with a traceable hybrid pipeline that combines structured rule filtering, vector ranking, and grounded explanation.

## 4. Objectives

### 4.1 Product objectives

- Provide personalized youth-policy discovery from official public data.
- Improve access to policy eligibility, benefits, procedures, and documents.
- Support natural-language policy exploration without relying on keyword matching alone.
- Preserve official sources so users can verify every recommendation.
- Communicate unknown or ambiguous conditions instead of overclaiming eligibility.

### 4.2 Learning and portfolio objectives

- Implement a reproducible public-data collection and normalization pipeline.
- Design a SQLite schema and traceable policy-data model.
- Implement deterministic filtering and FAISS semantic retrieval.
- Build a grounded OpenAI API integration.
- Develop and deploy a usable Streamlit prototype.
- Evaluate recommendation quality with measurable scenarios and tests.

## 5. Target users

Primary users are young adults searching for central-government or local-government support related to:

- Employment and job preparation
- Housing and moving expenses
- Education and training
- Finance and asset building
- Welfare and living support
- Entrepreneurship or other youth-support categories

The initial prototype is designed for a general Korean-speaking user. It does not require account creation or storage of a personal profile.

## 6. MVP scope

### 6.1 Included

The MVP includes:

- Primary policy data from the 온통청년 청년정책 API
- Timestamped preservation of raw API responses
- Reproducible normalization into canonical policy fields
- Processed storage in CSV and SQLite
- User inputs for age, region, income condition, employment status, education status, interests, and optional free-text request
- Tri-state rule evaluation: `MATCH`, `NO_MATCH`, `UNKNOWN`
- Hard filtering only where source data is sufficiently reliable
- FAISS semantic ranking of filtered candidates
- OpenAI API-generated grounded explanations
- Top-5 recommendation display by default
- Official source URL and verification date display
- Closed-policy exclusion when closure can be determined reliably
- Clear eligibility disclaimer and uncertainty display
- pytest-based automated tests
- Streamlit Community Cloud deployment target

### 6.2 Excluded from the initial MVP

- FastAPI
- MySQL or PostgreSQL
- ChromaDB
- Selenium-based large-scale crawling
- Concurrent integration of 온통청년, 복지로, 서울, 경기, and other sources
- User authentication or account management
- Persistent personal profile storage
- Policy application submission or document upload
- Automatic application, reservation, payment, or notification execution
- Administrator dashboard
- Native mobile app

### 6.3 Optional extensions after MVP completion

Only after the MVP is verified:

- Add 복지로 or 서울시 policy data through a separate adapter
- Separate recommendation logic into FastAPI
- Migrate structured storage to PostgreSQL or MySQL
- Add scheduled data refresh
- Add policy bookmarks or non-sensitive local preferences
- Add monitoring, analytics, or a simple admin data-quality screen

## 7. Fixed technology stack

| Area | Decision |
|---|---|
| Language | Python 3.10 |
| Web application | Streamlit |
| HTTP collection | Requests |
| Data processing | Pandas |
| Structured storage | raw API JSON/XML snapshots, processed CSV, and SQLite processed database |
| Vector search | FAISS |
| Vector artifacts | FAISS index and policy ID mapping data |
| Embeddings | OpenAI API, default `text-embedding-3-small` |
| Explanation generation | OpenAI API, model selected by environment variable |
| Tests | pytest |
| Deployment | Streamlit Community Cloud |

The application remains a single Streamlit service for the MVP. FastAPI and external relational databases are intentionally deferred to reduce deployment and integration risk.

## 8. High-level architecture

```text
온통청년 API
  ↓
Raw JSON/XML snapshot
  ↓
Pandas normalization and validation
  ↓
Processed CSV + SQLite
  ↓
Embedding text construction
  ↓
OpenAI embedding generation
  ↓
FAISS index + policy_id mapping

User profile + natural-language request
  ↓
Rule evaluation (MATCH / NO_MATCH / UNKNOWN)
  ↓
Candidate filtering
  ↓
FAISS semantic ranking
  ↓
Top policy records with official metadata
  ↓
Grounded OpenAI explanation
  ↓
Streamlit result cards + disclaimer + sources
```

## 9. Data-source strategy

### 9.1 Primary source

Use the official 온통청년 youth-policy API as the initial source. The source-domain reference should use the current 온통청년 service (`youthcenter.go.kr`) rather than the outdated `korea-youth.go.kr` wording from an earlier plan.

### 9.2 Collection requirements

- Store each raw response in a timestamped file.
- Record collection time, source name, request parameters, and response format.
- Never overwrite a previous raw snapshot.
- Detect and report API errors, malformed responses, empty responses, and rate-limit failures.
- Avoid collecting more data than needed during development.
- Support a small sample mode for local testing.

### 9.3 Manual supplementation

Missing required documents or application procedures may be supplemented only when verified against an official source.

Supplemented values must include:

- Official source URL
- Verification date
- A clear distinction between source-provided and manually normalized content

Do not infer missing official facts from blogs, commercial pages, or LLM output.

### 9.4 Future sources

복지로 and Seoul youth-policy sources are future adapters. Their schemas must not be mixed into the primary pipeline until the 온통청년 end-to-end flow is stable and tested.

## 10. Canonical policy data model

The processed dataset uses the following fields.

| Field | Intended type | Description |
|---|---|---|
| `policy_id` | string | Stable unique identifier used across SQLite and FAISS mapping |
| `policy_name` | string | Official policy title |
| `category` | string/null | Normalized policy category |
| `summary` | string/null | Concise source-grounded policy summary |
| `region_code` | string/null | Official or normalized region code |
| `region_name` | string/null | Human-readable region |
| `age_min` | integer/null | Minimum eligible age when reliably extractable |
| `age_max` | integer/null | Maximum eligible age when reliably extractable |
| `income_condition` | string/null | Official income condition text or normalized label |
| `employment_status` | string/null | Official employment condition text or normalized value |
| `education_status` | string/null | Official education condition text or normalized value |
| `application_start` | date/null | Application start date |
| `application_end` | date/null | Application end date |
| `application_status` | string | Derived or source status: `upcoming`, `open`, `closed`, `unknown` |
| `eligibility_text` | string/null | Original or safely combined eligibility text |
| `benefit_text` | string/null | Official benefit/support content |
| `application_method` | string/null | Official application procedure |
| `required_documents` | string/null | Official required-document information |
| `contact` | string/null | Official contact information |
| `source_name` | string | Source organization or platform |
| `source_url` | string/null | Official policy or source URL |
| `last_verified_at` | date/datetime | Latest collection or manual verification time |
| `embedding_text` | string | Deterministically constructed text used for embeddings |

### 10.1 Data-model rules

- `policy_id` must remain stable between processed data and FAISS metadata.
- Missing values remain null or empty according to one documented convention.
- Do not replace missing official facts with generated content.
- Preserve original source fields needed to audit mappings.
- Normalize dates to `YYYY-MM-DD` where possible.
- Derive `application_status` from dates using the current date when dates are reliable; otherwise use `unknown`.
- The `embedding_text` rule must be deterministic and versioned in code or metadata.

## 11. User input model

The initial Streamlit form should support:

- Age
- Residence region
- Income condition or income bracket, including “모름/확인 필요”
- Employment status
- Education status
- Interest category or categories
- Optional natural-language request

Input design rules:

- Do not request a resident registration number, exact address, bank details, or other unnecessary sensitive data.
- Allow unknown selections rather than forcing users to guess.
- Explain that inputs are used only for the current recommendation session in the MVP.
- Validate age and required fields with clear Korean messages.

## 12. Rule-based filtering design

### 12.1 Tri-state result

Each evaluated condition returns:

- `MATCH`: available data supports the condition.
- `NO_MATCH`: available data clearly contradicts the condition.
- `UNKNOWN`: data is missing, ambiguous, or unsafe to parse.

### 12.2 Hard-filter candidates

The following may be hard filters only when reliable structured data exists:

- Age range
- Region restriction
- Application status or confirmed application end date

A policy with a clear `NO_MATCH` on a mandatory hard condition may be excluded.

### 12.3 Soft or uncertain conditions

The following often appear as free text and should not automatically exclude a policy unless the source mapping is reliable:

- Income condition
- Employment status
- Education status
- Household or special-category requirements

For these fields:

- Keep `UNKNOWN` candidates.
- Record the uncertain condition.
- Display it under “확인이 필요한 조건”.

### 12.4 Explanation trace

For every recommended policy, retain:

- Matched conditions
- Clear non-matches considered during filtering
- Unknown or unverified conditions
- Reason the policy remained in the candidate set

This trace supports the UI, automated tests, and final report evaluation.

## 13. Semantic search design

### 13.1 Embedding content

`embedding_text` should be constructed from available official fields such as:

- Policy name
- Category
- Summary
- Eligibility text
- Benefit text
- Application method
- Region name

Do not include generated recommendations in the embedding source.

### 13.2 Indexing

- Generate embeddings offline or through an explicit build command.
- Store the FAISS index separately from a metadata mapping.
- Maintain an ordered mapping from vector position to `policy_id`.
- Validate that the number of vectors equals the number of mapped policy IDs.
- Rebuild the index when processed source data or the embedding model changes.
- Record the embedding model and build time in index metadata.

### 13.3 Ranking

- Apply rule filtering before semantic ranking.
- Rank only the remaining candidate records.
- Return Top-5 results by default.
- Handle fewer than five candidates gracefully.
- Define deterministic tie handling where practical.

## 14. LLM explanation design

### 14.1 Allowed role

The LLM may:

- Summarize retrieved official policy information.
- Explain why a retrieved policy appears relevant.
- Separate matched and uncertain conditions.
- Reformat application procedure and required documents for readability.
- State that final eligibility requires official confirmation.

### 14.2 Prohibited role

The LLM must not:

- Retrieve or introduce unprovided policies.
- Decide final eligibility.
- Invent missing values.
- Change dates, benefit amounts, application instructions, or documents.
- Hide uncertainty.
- Cite unofficial sources as official facts.

### 14.3 Prompt requirements

The prompt must:

- Include only the selected policy records and user-provided conditions needed for the explanation.
- Explicitly forbid unsupported additions.
- Require unknown values to be described as confirmation items.
- Require official source URL preservation.
- Prefer a structured response that can be validated before display.

### 14.4 Failure behavior

If explanation generation fails:

- Continue to display retrieved policy data.
- Show a clear message that AI explanation is temporarily unavailable.
- Do not discard official source information.
- Log a sanitized error without secrets or sensitive user inputs.

## 15. Recommendation result requirements

Each result card must show, when available:

- 정책명
- 추천 이유
- 일치한 조건
- 확인이 필요한 조건
- 지원 내용
- 신청 기간 and current status
- 신청 방법
- 필요 서류
- 공식 출처 link
- 최종 확인 날짜

The page must display this disclaimer prominently:

> 지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.

Result wording must distinguish:

- Official source fields
- Deterministic rule results
- AI-generated explanation

## 16. Streamlit UI requirements

The MVP should include:

1. Project title and short description
2. Eligibility disclaimer
3. User-condition input form
4. Optional natural-language request
5. Search/recommend button
6. Loading and progress feedback
7. Top result cards
8. Matched and uncertain condition sections
9. Official-source links
10. Empty-result guidance
11. Clear error states for missing configuration or unavailable services

Usability rules:

- Use Korean labels and plain language.
- Do not overload the first screen with technical details.
- Keep forms readable on a laptop screen.
- Avoid implying that the service is an official government determination.
- Provide a clear way to modify conditions and search again.

## 17. Error handling requirements

Provide user-friendly handling for:

- Missing OpenAI API key
- Missing or unreadable SQLite database
- Missing or mismatched FAISS index metadata
- Public API network failure
- Empty API response
- No policies after hard filtering
- No valid semantic-search candidates
- LLM timeout or invalid response
- Malformed dates or missing source URLs

Errors should identify the failed stage without exposing secrets or raw stack traces to end users.

## 18. Configuration and secrets

Expected environment variables:

```text
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Rules:

- Local secrets belong in `.env` or `.streamlit/secrets.toml`.
- Deployment secrets belong in Streamlit Community Cloud secret settings.
- `.env.example` contains names and safe placeholders only.
- The chat model remains configurable; documentation must not permanently compare or lock the project to GPT-4o or any other chat model.
- The application should show a clear configuration message when required values are missing.

## 19. Proposed repository structure

This is a target structure, not proof that files already exist:

```text
career-catch-4/
├─ AGENTS.md
├─ PROJECT_SPEC.md
├─ TASKS.md
├─ README.md
├─ app.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ indexes/
├─ scripts/
│  ├─ fetch_policies.py
│  ├─ build_dataset.py
│  └─ build_index.py
├─ src/
│  └─ career_catch/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ models.py
│     ├─ collection.py
│     ├─ normalization.py
│     ├─ storage.py
│     ├─ filtering.py
│     ├─ retrieval.py
│     ├─ explanation.py
│     └─ service.py
├─ tests/
│  ├─ fixtures/
│  ├─ test_normalization.py
│  ├─ test_filtering.py
│  ├─ test_storage.py
│  └─ test_retrieval.py
└─ docs/
```

The exact structure may be simplified during implementation, but architecture changes require an explicit reason and user approval when they affect scope or dependencies.

## 20. Testing strategy

### 20.1 Unit tests

Test at least:

- API field mapping into canonical fields
- Duplicate handling by `policy_id`
- Null and malformed source values
- Date normalization and application-status derivation
- Age and region hard filters
- Income, employment, and education `UNKNOWN` behavior
- Closed-policy exclusion
- Matched and uncertain reason traces
- FAISS vector-to-policy mapping integrity
- No-network behavior through mocks
- LLM response validation or safe fallback behavior

### 20.2 Integration tests

Use a small fixed policy fixture to verify:

```text
User input
→ rule evaluation
→ candidate set
→ semantic ranking
→ grounded explanation request construction
→ result view model
```

Integration tests must not require a real OpenAI API call by default.

### 20.3 Manual checks

- Launch the Streamlit app locally.
- Complete at least three representative input scenarios.
- Verify source links.
- Verify closed-policy behavior.
- Verify missing-key behavior.
- Verify the app remains useful when LLM explanation fails.

## 21. Evaluation plan

Prepare approximately 10–20 synthetic user scenarios. Initial examples include:

- 24 years old, Seoul, unemployed, income at or below a specified threshold, housing interest
- 29 years old, Gyeonggi, employed, no known income restriction, asset-building interest
- 22 years old, Busan, university student, education or certification interest

Evaluate:

- Clear non-matching policy exclusion rate
- Expected-policy Top-5 inclusion rate
- Closed-policy exclusion accuracy
- Percentage of recommendations with an official source URL
- Percentage with a verification date
- Grounded explanation rate
- Unsupported-content or hallucination count
- Average end-to-end response time
- Number of uncertain conditions correctly surfaced instead of guessed

The final report may include verified results in a form such as:

```text
15개 시나리오 중 13개에서 기대 정책이 Top-5에 포함됨
Top-5 포함률: 86.7%
공식 출처 표시율: 100%
신청 마감 정책 오추천: 1건
```

These numbers are examples only. Do not use them as actual results until tests are run.

## 22. MVP acceptance criteria

The MVP is complete when all of the following are verified:

- A documented command collects or loads a valid 온통청년 sample.
- Raw responses are preserved without overwrite.
- Canonical processed data is reproducibly generated.
- SQLite contains queryable policy records with source traceability.
- FAISS index and `policy_id` mapping pass integrity checks.
- User inputs produce deterministic rule results.
- Clear hard-condition mismatches are excluded.
- Unknown conditions remain visible for confirmation.
- Top-5 semantic results are returned when candidates exist.
- LLM explanations use retrieved context only and have a safe fallback.
- Every displayed recommendation preserves official source information.
- The disclaimer is visible.
- Relevant automated tests pass.
- Local Streamlit execution is verified.
- Deployment instructions are accurate, and a deployed URL is recorded only after real deployment.

## 23. Privacy and security

- Collect only the minimum session inputs needed for recommendation.
- Do not request highly sensitive identifiers.
- Do not store user profiles in the MVP.
- Do not log exact user inputs if they may contain personal information.
- Never expose API keys in logs, error messages, screenshots, source code, or Git history.
- Use official URLs and safe link rendering.

## 24. Known limitations

The MVP will have these expected limitations:

- Coverage is initially limited to the primary 온통청년 source.
- Free-text conditions may remain ambiguous.
- Policy freshness depends on the latest collected snapshot and source accuracy.
- Semantic relevance does not guarantee administrative eligibility.
- LLM explanations can fail and require fallback behavior.
- Streamlit Community Cloud local filesystem changes are not durable.
- Final eligibility always depends on the official notice and responsible institution.

## 25. Documentation and evidence rules

- `README.md` must describe only verified features and commands.
- `TASKS.md` must reflect current status rather than a fictional completed history.
- Daily and final reports must use real screenshots, actual outputs, measured metrics, and real test results from this codebase.
- Do not fabricate commits, API results, evaluation scores, deployment URLs, or user-test evidence.
- Architecture diagrams may describe planned or implemented designs, but their status must be clear.

## 26. Immediate next-document expectations

After this specification and `AGENTS.md` are placed in the project root, the next project-planning task is to create:

- `TASKS.md`, containing only the current implementation status, the next approved task, completion checks, and deferred extensions
- An initial `README.md`, clearly labeling unimplemented features and placeholder setup instructions

No application code should be generated until those documents are reviewed and the user approves the first implementation task.
