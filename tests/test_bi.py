import pandas as pd
from analytics.bi import pipeline_summary, work_order_summary, cross_board


def test_pipeline_and_weighted_pipeline():
    deals = pd.DataFrame([
        {
            "Deal Status": "Open",
            "Sector": "Energy",
            "Tentative Close Date": pd.Timestamp("2026-08-15"),
            "Masked Deal value": 100.0,
            "Closure Probability": 0.5,
            "Deal Stage": "E. Proposal/Commercials Sent",
            "Client Code": "C1",
        },
        {
            "Deal Status": "Open",
            "Sector": "Mining",
            "Tentative Close Date": pd.Timestamp("2026-08-15"),
            "Masked Deal value": 50.0,
            "Closure Probability": 1.0,
            "Deal Stage": "F. Negotiations",
            "Client Code": "C2",
        },
    ])
    result = pipeline_summary(
        deals,
        sector="Energy",
        start="2026-07-01",
        end="2026-10-01",
    )
    assert result["open_deals"] == 1
    assert result["pipeline_value"] == 100.0
    assert result["weighted_pipeline"] == 50.0


def test_work_order_risk():
    wo = pd.DataFrame([
        {"Item Name": "A", "Execution Status": "Not Started"},
        {"Item Name": "B", "Execution Status": "Completed"},
        {"Item Name": "C", "Execution Status": None},
        {"Item Name": "D", "Execution Status": "Pause / Struck"},
    ])
    result = work_order_summary(wo)
    assert result["at_risk_count"] == 3


def test_cross_board_exact_code_match():
    deals = pd.DataFrame([
        {"Client Code": "C1", "Deal Status": "Open"},
        {"Client Code": "C2", "Deal Status": "Closed"},
    ])
    wo = pd.DataFrame([
        {"Customer Name Code": "C1", "Execution Status": "Ongoing"},
        {"Customer Name Code": "C3", "Execution Status": "Ongoing"},
    ])
    result = cross_board(deals, wo)
    assert result["overlap_count"] == 1
    assert result["overlap_customer_codes"] == ["C1"]
