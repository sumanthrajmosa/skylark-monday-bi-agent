import pandas as pd
from data.normalizer import normalize_sector, normalize_money

def test_sector(): assert normalize_sector(' energy sector ') == 'Energy'
def test_money(): assert normalize_money('₹1,234.50') == 1234.5
