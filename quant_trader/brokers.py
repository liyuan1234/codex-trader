from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass
class AccountSnapshot:
    cash_balance: float
    positions: dict[str, int]


@dataclass
class OrderRequest:
    symbol: str
    side: str
    quantity: int
    reference_price: float | None = None


@dataclass
class OrderReceipt:
    broker: str
    symbol: str
    side: str
    quantity: int
    submitted_at: str
    raw: dict = field(default_factory=dict)


class PaperBroker(Protocol):
    def get_account_snapshot(self) -> AccountSnapshot:
        raise NotImplementedError

    def place_market_order(self, order: OrderRequest) -> OrderReceipt:
        raise NotImplementedError


class SimulatedPaperBroker:
    def __init__(self, starting_cash: float = 0.0) -> None:
        self.cash_balance = float(starting_cash)
        self.positions: dict[str, int] = {}

    def get_account_snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(cash_balance=self.cash_balance, positions=dict(self.positions))

    def place_market_order(self, order: OrderRequest) -> OrderReceipt:
        signed_qty = order.quantity if order.side.upper() == "BUY" else -order.quantity
        self.positions[order.symbol] = self.positions.get(order.symbol, 0) + signed_qty
        if order.reference_price is not None:
            cash_change = float(order.reference_price) * order.quantity
            if order.side.upper() == "BUY":
                self.cash_balance -= cash_change
            else:
                self.cash_balance += cash_change
        return OrderReceipt(
            broker="simulated",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            submitted_at=datetime.now(UTC).isoformat(),
            raw={
                "positions": dict(self.positions),
                "cash_balance": self.cash_balance,
                "reference_price": order.reference_price,
            },
        )


class MoomooPaperBroker:
    def __init__(self, host: str, port: int, market: str, pwd_unlock: str = "") -> None:
        from moomoo import OpenSecTradeContext, SecurityFirm, TrdMarket, TrdSide, TrdEnv, OrderType, RET_OK

        self._OpenSecTradeContext = OpenSecTradeContext
        self._SecurityFirm = SecurityFirm
        self._TrdMarket = TrdMarket
        self._TrdSide = TrdSide
        self._TrdEnv = TrdEnv
        self._OrderType = OrderType
        self._RET_OK = RET_OK
        self.host = host
        self.port = port
        self.market = getattr(TrdMarket, market)
        self.pwd_unlock = pwd_unlock
        self._context_kwargs = {
            "filter_trdmarket": self.market,
            "host": host,
            "port": port,
            "security_firm": self._SecurityFirm.FUTUSG,
        }

    def get_account_snapshot(self) -> AccountSnapshot:
        ctx = self._OpenSecTradeContext(**self._context_kwargs)
        try:
            if self.pwd_unlock:
                ctx.unlock_trade(self.pwd_unlock)
            cash_balance = 0.0
            ret, account_data = ctx.accinfo_query(trd_env=self._TrdEnv.SIMULATE)
            if ret == self._RET_OK and hasattr(account_data, "iterrows"):
                first_row = next(account_data.iterrows(), (None, None))[1]
                if first_row is not None:
                    for candidate in ("cash", "cash_balance", "power", "net_cash_power"):
                        value = first_row.get(candidate)
                        if value not in (None, ""):
                            cash_balance = float(value)
                            break
            ret, data = ctx.position_list_query(position_market=self.market, trd_env=self._TrdEnv.SIMULATE)
            if ret != self._RET_OK:
                raise RuntimeError(f"moomoo position_list_query failed: {data}")
            positions: dict[str, int] = {}
            if hasattr(data, "iterrows"):
                for _, row in data.iterrows():
                    positions[str(row["code"])] = int(row["qty"])
            return AccountSnapshot(cash_balance=cash_balance, positions=positions)
        finally:
            ctx.close()

    def place_market_order(self, order: OrderRequest) -> OrderReceipt:
        ctx = self._OpenSecTradeContext(**self._context_kwargs)
        try:
            if self.pwd_unlock:
                ctx.unlock_trade(self.pwd_unlock)
            side = self._TrdSide.BUY if order.side.upper() == "BUY" else self._TrdSide.SELL
            ret, data = ctx.place_order(
                price=0,
                qty=order.quantity,
                code=order.symbol,
                trd_side=side,
                order_type=self._OrderType.MARKET,
                trd_env=self._TrdEnv.SIMULATE,
            )
            if ret != self._RET_OK:
                raise RuntimeError(f"moomoo place_order failed: {data}")
            raw = data.iloc[0].to_dict() if hasattr(data, "iloc") else {"response": str(data)}
            return OrderReceipt(
                broker="moomoo",
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                submitted_at=datetime.now(UTC).isoformat(),
                raw=raw,
            )
        finally:
            ctx.close()


def build_paper_broker(config: dict) -> PaperBroker:
    broker_name = str(config.get("broker", "simulated")).lower()
    if broker_name == "simulated":
        return SimulatedPaperBroker(starting_cash=float(config.get("starting_cash", 0.0)))
    if broker_name == "moomoo":
        return MoomooPaperBroker(
            host=str(config["moomoo_host"]),
            port=int(config["moomoo_port"]),
            market=str(config["moomoo_market"]),
            pwd_unlock=str(config.get("moomoo_pwd_unlock", "")),
        )
    raise ValueError(f"Unsupported paper broker: {broker_name}")
