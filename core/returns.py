from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from core.calculations import PortfolioValuePoint
from core.db import Transaction


@dataclass
class ReturnResult:
    label: str
    twr: Optional[float]
    mwr: Optional[float]


def compute_twr(values: Iterable[PortfolioValuePoint]) -> Optional[float]:
    values_list = list(values)
    if len(values_list) < 2:
        return None
    total = 1.0
    prev = values_list[0].value
    for point in values_list[1:]:
        if prev <= 0:
            prev = point.value
            continue
        total *= point.value / prev
        prev = point.value
    return (total - 1) * 100


def xnpv(rate: float, cashflows: list[tuple[datetime, float]]) -> float:
    if rate <= -1:
        return float("inf")
    start = cashflows[0][0]
    total = 0.0
    for dt, amount in cashflows:
        days = (dt - start).days
        total += amount / ((1 + rate) ** (days / 365.0))
    return total


def xirr(cashflows: list[tuple[datetime, float]]) -> Optional[float]:
    if not cashflows:
        return None
    if all(amount <= 0 for _, amount in cashflows) or all(
        amount >= 0 for _, amount in cashflows
    ):
        return None
    guess = 0.1
    for _ in range(50):
        if guess <= -0.9999:
            break
        f_value = xnpv(guess, cashflows)
        derivative = 0.0
        start = cashflows[0][0]
        for dt, amount in cashflows:
            days = (dt - start).days
            frac = days / 365.0
            base = 1 + guess
            if base <= 0:
                derivative = 0.0
                break
            derivative -= (frac * amount) / (base ** (frac + 1))
        if derivative == 0:
            break
        new_guess = guess - f_value / derivative
        if new_guess <= -0.9999:
            break
        if abs(new_guess - guess) < 1e-6:
            return new_guess * 100
        guess = new_guess

    low, high = -0.9999, 10.0
    for _ in range(100):
        mid = (low + high) / 2
        value = xnpv(mid, cashflows)
        if abs(value) < 1e-5:
            return mid * 100
        if value > 0:
            low = mid
        else:
            high = mid
    return None


def _slice_values(
    values: list[PortfolioValuePoint], start_date: datetime
) -> list[PortfolioValuePoint]:
    return [
        point
        for point in values
        if datetime.fromisoformat(point.date) >= start_date
    ]


def _value_on_or_before(
    values: list[PortfolioValuePoint], target: datetime
) -> Optional[PortfolioValuePoint]:
    candidates = [
        point
        for point in values
        if datetime.fromisoformat(point.date) <= target
    ]
    return candidates[-1] if candidates else None


def compute_returns(
    values: list[PortfolioValuePoint],
    transactions: list[Transaction],
) -> list[ReturnResult]:
    if not values:
        return []

    end_date = datetime.fromisoformat(values[-1].date)
    periods = [
        ("1D", end_date - timedelta(days=1)),
        ("1W", end_date - timedelta(weeks=1)),
        ("1M", end_date - timedelta(days=30)),
        ("3M", end_date - timedelta(days=90)),
        ("6M", end_date - timedelta(days=180)),
        ("1Y", end_date - timedelta(days=365)),
        ("3Y", end_date - timedelta(days=365 * 3)),
        ("5Y", end_date - timedelta(days=365 * 5)),
    ]
    ytd_start = datetime(end_date.year, 1, 1)
    periods.insert(0, ("YTD", ytd_start))
    periods.append(("Od początku", datetime.fromisoformat(values[0].date)))

    results: list[ReturnResult] = []
    for label, start in periods:
        if start > end_date:
            results.append(ReturnResult(label=label, twr=None, mwr=None))
            continue
        sliced = _slice_values(values, start)
        if len(sliced) < 2:
            results.append(ReturnResult(label=label, twr=None, mwr=None))
            continue
        twr = compute_twr(sliced)
        start_value_point = _value_on_or_before(values, start)
        if not start_value_point:
            results.append(ReturnResult(label=label, twr=twr, mwr=None))
            continue
        cashflows: list[tuple[datetime, float]] = [
            (datetime.fromisoformat(start_value_point.date), -start_value_point.value)
        ]
        for tx in transactions:
            tx_date = datetime.fromisoformat(tx.trade_date)
            if tx_date < start:
                continue
            cashflows.append(
                (tx_date, -(tx.quantity * tx.price + (tx.fee or 0.0)))
            )
        cashflows.append((end_date, values[-1].value))
        cashflows.sort(key=lambda item: item[0])
        mwr = xirr(cashflows)
        results.append(ReturnResult(label=label, twr=twr, mwr=mwr))
    return results
