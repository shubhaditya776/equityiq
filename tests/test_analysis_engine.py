from analysis_engine import rule_based_insights


def test_growth_and_debt_flags():
    o = {
        'QuarterlyRevenueGrowthYOY': '-0.10',
        'QuarterlyEarningsGrowthYOY': '-0.20',
        'ReturnOnEquityTTM': '0.15',
        'ProfitMargin': '0.08',
        'DebtToEquity': '1.4',
        'PERatio': '45',
    }
    insights, flags = rule_based_insights(o)
    assert any('Revenue growth' in x for x in insights)
    assert any('Revenue contraction' in x for x in flags)
    assert any('Debt-to-equity' in x for x in flags)
    assert any('high P/E' in x for x in flags)
