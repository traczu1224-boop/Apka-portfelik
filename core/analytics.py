from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import pstdev
from typing import Iterable, Optional

from core.calculations import PortfolioValuePoint


@dataclass
class RiskMetrics:
    max_drawdown_pct: Optional[float]
    volatility_pct: Optional[float]


def compute_risk_metrics(values: Iterable[PortfolioValuePoint]) -> RiskMetrics:
    values_list = list(values)
    if len(values_list) < 2:
        return RiskMetrics(max_drawdown_pct=None, volatility_pct=None)

    series = [point.value for point in values_list]
    peak = series[0]
    max_drawdown = 0.0
    for value in series:
        if value > peak:
            peak = value
        drawdown = (value - peak) / peak if peak else 0.0
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    returns = []
    for prev, current in zip(series, series[1:]):
        if prev <= 0:
            continue
        returns.append((current / prev) - 1)
    volatility = None
    if len(returns) >= 2:
        volatility = pstdev(returns) * sqrt(252) * 100

    return RiskMetrics(
        max_drawdown_pct=abs(max_drawdown) * 100,
        volatility_pct=volatility,
    )
