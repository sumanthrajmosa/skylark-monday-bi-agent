# Skylark Drones — Monday.com Business Intelligence Agent

## Architecture
Streamlit UI → BI Agent → Monday.com GraphQL API (read-only) → normalization/data-quality layer → deterministic BI metrics → OpenAI response layer.

The application does **not** hardcode the supplied Excel/CSV business data. Monday.com is the runtime source of truth.

## Monday.com setup
Create two boards by importing the supplied datasets as separate boards.

### Work Orders board
Recommended column types:
- Deal name masked — Item name
- Customer Name Code — Text
- Serial # — Text
- Nature of Work — Status/Text
- Last executed month of recurring project — Text
- Execution Status — Status
- Data Delivery Date — Date
- Date of PO/LOI — Date
- Document Type — Status/Text
- Probable Start Date — Date
- Probable End Date — Date
- BD/KAM Personnel code — Text
- Sector — Status/Text
- Type of Work — Text
- Skylark software platform — Status/Text
- Last invoice date — Date
- latest invoice no. — Text
- Amount / billed / collected / receivable fields — Numbers
- Quantity fields — Numbers/Text where units are embedded
- Invoice Status — Status/Text
- Expected/Actual Billing Month — Text or Date
- WO Status (billed) — Status
- Collection status — Status
- Collection Date — Date
- Billing Status — Status

### Deals board
Recommended column types:
- Deal Name — Item name
- Owner code — Text
- Client Code — Text
- Deal Status — Status
- Close Date (A) — Date
- Closure Probability — Status
- Masked Deal value — Numbers
- Tentative Close Date — Date
- Deal Stage — Status
- Product deal — Text
- Sector/service — Status/Text
- Created Date — Date

## Environment
Copy `.env.example` to `.env` and fill values. For deployment, configure the same variables as platform secrets/environment variables.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Read-only integration
The agent uses Monday's GraphQL API only for board reads. No create/update/delete mutations are used.

## Data resilience
- whitespace/case normalization
- sector normalization
- date coercion with invalid values becoming missing
- numeric parsing
- missing values remain missing, not zero
- quality counts are calculated at runtime
- API errors are surfaced gracefully

## Leadership updates
A leadership update is interpreted as a concise executive brief containing a headline, key commercial/operational metrics, material wins and risks, data-quality caveats, and recommended next actions.

## Deployment
Streamlit Community Cloud is the simplest hosted option: connect this repository, set the environment variables/secrets, and deploy `app.py`.
