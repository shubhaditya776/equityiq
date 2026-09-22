import pandas as pd


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def fundamentals_table(o: dict) -> pd.DataFrame:
    rows = [
        ("Revenue TTM", o.get("RevenueTTM")),
        ("EBITDA", o.get("EBITDA")),
        ("EPS", o.get("EPS")),
        ("P/E", o.get("PERatio")),
        ("P/B", o.get("PriceToBookRatio")),
        ("EV/EBITDA", o.get("EVToEBITDA")),
        ("ROE", o.get("ReturnOnEquityTTM")),
        ("Profit Margin", o.get("ProfitMargin")),
        ("Operating Margin", o.get("OperatingMarginTTM")),
        ("Revenue Growth YoY", o.get("QuarterlyRevenueGrowthYOY")),
        ("Earnings Growth YoY", o.get("QuarterlyEarningsGrowthYOY")),
        ("Debt/Equity", o.get("DebtToEquity")),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def rule_based_insights(o: dict):
    insights = []
    growth = safe_float(o.get("QuarterlyRevenueGrowthYOY"))
    earnings = safe_float(o.get("QuarterlyEarningsGrowthYOY"))
    roe = safe_float(o.get("ReturnOnEquityTTM"))
    margin = safe_float(o.get("ProfitMargin"))
    debt = safe_float(o.get("DebtToEquity"))
    pe = safe_float(o.get("PERatio"))

    if growth is not None:
        insights.append(f"Revenue growth YoY is {growth*100:.1f}%.")
    if earnings is not None:
        insights.append(f"Earnings growth YoY is {earnings*100:.1f}%.")
    if roe is not None:
        insights.append(f"ROE is {roe*100:.1f}%.")
    if margin is not None:
        insights.append(f"Net profit margin is {margin*100:.1f}%.")
    if debt is not None:
        insights.append(f"Debt-to-equity is {debt:.2f}.")
    if pe is not None:
        insights.append(f"Reported trailing P/E is {pe:.2f}x.")

    flags=[]
    if growth is not None and growth < 0: flags.append("Revenue contraction requires investigation.")
    if earnings is not None and earnings < 0: flags.append("Earnings contraction requires investigation.")
    if debt is not None and debt > 1: flags.append("Debt-to-equity above 1.0 warrants balance-sheet review.")
    if pe is not None and pe > 40: flags.append("A high P/E can imply elevated expectations; compare with peers and growth.")
    if margin is not None and margin < 0: flags.append("Negative net margin indicates reported losses.")

    return insights, flags
