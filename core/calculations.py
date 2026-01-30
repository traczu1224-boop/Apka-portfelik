from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, Optional

from core.db import PriceRow, Transaction


@dataclass
class PositionSummary:
    symbol: str
    currency: str
    quantity: float
    total_cost: float
    average_cost: float
    last_price: Optional[float]
    last_price_date: Optional[str]
    market_value: Optional[float]
    profit_loss: Optional[float]
    profit_loss_pct: Optional[float]


@dataclass
class PortfolioValuePoint:
    date: str
    value: float


def aggregate_positions(
    transactions: Iterable[Transaction], latest_prices: Dict[str, Optional[PriceRow]]
) -> list[PositionSummary]:
    buckets: Dict[str, dict] = {}
    for tx in transactions:
        bucket = buckets.setdefault(
            tx.symbol,
            {"quantity": 0.0, "cost": 0.0, "currency": tx.currency},
        )
        bucket["quantity"] += tx.quantity
        bucket["cost"] += tx.quantity * tx.price + (tx.fee or 0.0)
        if not bucket.get("currency"):
            bucket["currency"] = tx.currency

    summaries: list[PositionSummary] = []
    for symbol, data in buckets.items():
        quantity = data["quantity"]
        total_cost = data["cost"]
        average_cost = total_cost / quantity if quantity else 0.0
        price_row = latest_prices.get(symbol)
        last_price = price_row.close if price_row else None
        last_price_date = price_row.date if price_row else None
        market_value = quantity * last_price if last_price is not None else None
        profit_loss = None
        profit_loss_pct = None
        if market_value is not None:
            profit_loss = market_value - total_cost
            profit_loss_pct = (profit_loss / total_cost) * 100 if total_cost else None
        summaries.append(
            PositionSummary(
                symbol=symbol,
                currency=data["currency"],
                quantity=quantity,
                total_cost=total_cost,
                average_cost=average_cost,
                last_price=last_price,
                last_price_date=last_price_date,
                market_value=market_value,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct,
            )
        )
    return sorted(summaries, key=lambda item: item.symbol)


def compute_portfolio_history(
    transactions: Iterable[Transaction],
    prices_by_symbol: Dict[str, list[PriceRow]],
) -> list[PortfolioValuePoint]:
    tx_list = list(transactions)
    if not tx_list:
        return []

    start_date = min(datetime.fromisoformat(tx.trade_date).date() for tx in tx_list)
    end_date_candidates = [
        datetime.fromisoformat(prices[-1].date).date()
        for prices in prices_by_symbol.values()
        if prices
    ]
    if not end_date_candidates:
        end_date_candidates = [date.today()]
    end_date = max(end_date_candidates)

    tx_by_symbol: Dict[str, list[Transaction]] = {}
    for tx in sorted(tx_list, key=lambda item: item.trade_date):
        tx_by_symbol.setdefault(tx.symbol, []).append(tx)

    price_idx: Dict[str, int] = {symbol: 0 for symbol in prices_by_symbol}
    last_price: Dict[str, Optional[float]] = {symbol: None for symbol in prices_by_symbol}
    tx_idx: Dict[str, int] = {symbol: 0 for symbol in tx_by_symbol}
    holdings: Dict[str, float] = {symbol: 0.0 for symbol in tx_by_symbol}

    history: list[PortfolioValuePoint] = []
    current_date = start_date
    while current_date <= end_date:
        for symbol, txs in tx_by_symbol.items():
            while tx_idx[symbol] < len(txs):
                tx = txs[tx_idx[symbol]]
                tx_date = datetime.fromisoformat(tx.trade_date).date()
                if tx_date > current_date:
                    break
                holdings[symbol] += tx.quantity
                tx_idx[symbol] += 1

        for symbol, prices in prices_by_symbol.items():
            while price_idx[symbol] < len(prices):
                price_row = prices[price_idx[symbol]]
                price_date = datetime.fromisoformat(price_row.date).date()
                if price_date > current_date:
                    break
                last_price[symbol] = price_row.close
                price_idx[symbol] += 1

        total_value = 0.0
        for symbol, qty in holdings.items():
            if qty == 0:
                continue
            price = last_price.get(symbol)
            if price is None:
                continue
            total_value += qty * price

        history.append(
            PortfolioValuePoint(date=current_date.isoformat(), value=total_value)
        )
        current_date += timedelta(days=1)

    return history
