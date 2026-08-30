# Decision Log — Skylark Drones Monday.com BI Agent

## 1. Key assumptions
- Monday.com is the runtime source of truth; the supplied spreadsheets are used to design and validate the schema, not embedded as application data.
- The two boards are the minimum required sources: Work Orders for execution/billing and Deals for sales pipeline.
- Deal value is treated as the pipeline amount when a value is present. Missing deal value is excluded from totals and reported as a data-quality issue rather than treated as zero.
- Weighted pipeline uses High/Medium/Low probabilities of 100%/50%/25% when an explicit probability is present. This is an assumption because the source data does not provide numeric probabilities.
- "This quarter" is interpreted using the current date and the Tentative Close Date for open deals.

## 2. Trade-offs
- **Streamlit + Python** was chosen over a heavier frontend because the assignment prioritizes a testable conversational prototype and rapid deployment.
- **Monday GraphQL API** was chosen because it gives direct, dynamic board reads and keeps the integration read-only.
- Deterministic normalization and metric calculations are kept outside the LLM to reduce hallucinations and make business numbers reproducible.
- The LLM is used for query interpretation, narrative synthesis and leadership framing rather than as the calculator.
- The prototype reads the boards at request time. A production system could add short-lived caching for speed while preserving freshness.

## 3. Data resilience
The supplied Work Orders data contains substantial missingness in fields such as delivery dates, invoice details, quantities and collection fields. Deals also have missing close dates, probabilities and deal values. The agent preserves nulls, normalizes text/dates, and surfaces material missing-data caveats.

## 4. Leadership updates
I interpreted the optional requirement as an executive-ready brief: one headline, the most important commercial and operational KPIs, notable wins, risks/blockers, data-quality caveats, and 2–3 recommended actions. This keeps the output decision-oriented instead of turning it into a raw dashboard dump.

## 5. What I would do with more time
- Add robust Monday pagination for boards larger than the first API page.
- Add schema auto-discovery and column-ID mapping so renamed columns do not break the agent.
- Add a semantic metric layer with definitions approved by finance/sales/operations.
- Add authentication for the hosted UI and audit logging.
- Add unit/integration tests against a mocked Monday API.
- Add charts and downloadable leadership briefs.
- Add explicit fiscal-quarter configuration instead of assuming calendar quarters.
