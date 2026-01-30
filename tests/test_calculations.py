from datetime import datetime, timedelta

from core.calculations import aggregate_positions, PortfolioValuePoint
from core.db import Transaction
from core.returns import compute_twr, xirr


def test_average_cost_with_fee():
    transactions = [
        Transaction(
            id=1,
            symbol="AAA",
            trade_date="2024-01-01",
            quantity=10.0,
            price=100.0,
            currency="PLN",
            fee=5.0,
        ),
        Transaction(
            id=2,
            symbol="AAA",
            trade_date="2024-01-02",
            quantity=5.0,
            price=120.0,
            currency="PLN",
            fee=0.0,
        ),
    ]
    positions = aggregate_positions(transactions, latest_prices={})
    assert len(positions) == 1
    position = positions[0]
    total_cost = 10 * 100 + 5 + 5 * 120
    expected_avg = total_cost / 15
    assert abs(position.average_cost - expected_avg) < 1e-6


def test_twr_simple_case():
    values = [
        PortfolioValuePoint(date="2024-01-01", value=100.0),
        PortfolioValuePoint(date="2024-01-02", value=110.0),
        PortfolioValuePoint(date="2024-01-03", value=121.0),
    ]
    twr = compute_twr(values)
    assert twr is not None
    assert abs(twr - 21.0) < 1e-6


def test_xirr_simple_case():
    start = datetime(2024, 1, 1)
    cashflows = [
        (start, -1000.0),
        (start + timedelta(days=365), 1100.0),
    ]
    result = xirr(cashflows)
    assert result is not None
    assert abs(result - 10.0) < 0.1
