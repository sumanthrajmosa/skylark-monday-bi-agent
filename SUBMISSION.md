# Skylark Drones — Submission Checklist

## Hosted Prototype

https://skylark-monday-bi-agent.streamlit.app/

## Source Code

GitHub repository:

https://github.com/sumanthrajmosa/skylark-monday-bi-agent

## Included documentation

- `README.md`
- `docs/decision_log.md`

## Local validation snapshot

- 175 Work Orders
- 344 Deals
- 49 Open Deals
- ₹688,152,293.17 gross open pipeline
- ₹313,338,834.20 weighted pipeline
- 20 Work Orders flagged by the defined operational-risk rules

These are validation-time observations from the live boards, not hardcoded application data.

## Security checklist

- [ ] Never commit `.env`.
- [ ] Never place Monday or Gemini API keys in source code.
- [ ] Use Streamlit secrets for the hosted deployment.
- [ ] Keep Monday integration read-only.

## Suggested evaluator demo questions

1. How many work orders are there?
2. How many deals are there?
3. What is our total open pipeline and weighted pipeline?
4. How is our pipeline looking for the Energy sector this quarter?
5. Which projects are operationally at risk?
6. Which customers have both open deals and active work orders?
7. Give me a leadership update for the business.
8. How reliable is the current data?
