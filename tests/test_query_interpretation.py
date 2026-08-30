import pandas as pd
from agent.agent import BIAGent


def test_energy_filter_detected_even_if_category_absent():
    deals = pd.DataFrame({"Sector": ["Mining", "Powerline", "Renewables"]})
    sector, start, end, label = BIAGent.extract_filters(
        "How is our pipeline looking for the Energy sector this quarter?", deals
    )
    assert sector == "Energy"
    assert label == "this quarter"
    assert start.month == 7
    assert end.month == 10


def test_sector_query_detection_without_sector_column():
    deals = pd.DataFrame({"Deal Status": ["Open"]})
    sector, start, end, label = BIAGent.extract_filters(
        "How is our pipeline looking for the Energy sector this quarter?", deals
    )
    assert sector == "Energy"
    assert label == "this quarter"
