from valuation.bank_valuation import (
    calculate_cost_of_equity,
    calculate_fair_pb,
    value_bank_pb_method,
    value_bank_residual_income,
    generate_valuation_scenarios,
)


def test_cost_of_equity():
    # Rf=4.5%, Beta=0.85, ERP=8.0% => Ke = 4.5% + 0.85 * 8% = 11.3%
    ke = calculate_cost_of_equity(rf=0.045, beta=0.85, erp=0.08)
    assert round(ke, 4) == 0.1130


def test_fair_pb_calculation():
    # ROE=20%, Ke=11.3%, g=6% => Fair PB = (20% - 6%) / (11.3% - 6%) = 14% / 5.3% ≈ 2.64
    fair_pb = calculate_fair_pb(roe=0.20, cost_of_equity=0.113, growth_rate=0.06)
    assert 2.6 <= fair_pb <= 2.7


def test_vcb_scenarios():
    bvps = 35000.0  # Giả định BVPS VCB ~ 35.000 đ
    current_price = 85000.0  # Giá thị trường giả định 85.000 đ
    scenarios = generate_valuation_scenarios(bvps=bvps, current_price=current_price)

    assert "bear" in scenarios
    assert "base" in scenarios
    assert "bull" in scenarios
    assert scenarios["base"]["target_price"] == 35000.0 * 2.8
    assert scenarios["bull"]["target_price"] > scenarios["base"]["target_price"]
