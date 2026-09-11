from ratio_engine.compute import StatementInput, compute_all_ratios


def _sample_statement() -> StatementInput:
    return StatementInput(
        revenue=1000,
        net_profit=100,
        total_assets=2000,
        total_liabilities=800,
        total_equity=1200,
        current_assets=600,
        current_liabilities=400,
        cash_from_operations=120,
    )


def test_compute_all_ratios_keys():
    ratios = compute_all_ratios(_sample_statement())
    expected_keys = {
        "current_ratio", "quick_ratio", "debt_to_equity", "debt_to_asset",
        "roe", "roa", "net_profit_margin", "asset_turnover", "cfo_to_net_income",
    }
    assert set(ratios.keys()) == expected_keys


def test_roe_value():
    ratios = compute_all_ratios(_sample_statement())
    assert ratios["roe"] == 100 / 1200
