from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class OrderRequest:
    symbol: str
    side: str
    quantity: int


@dataclass
class OrderReceipt:
    broker: str
    symbol: str
    side: str
    quantity: int
    submitted_at: str
    raw: dict = field(default_factory=dict)


class PaperBroker(Protocol):
    def place_market_order(self, order: OrderRequest) -> OrderReceipt:
        raise NotImplementedError


class SimulatedPaperBroker:
    def __init__(self) -> None:
        self.positions: dict[str, int] = {}

    def place_market_order(self, order: OrderRequest) -> OrderReceipt:
        signed_qty = order.quantity if order.side.upper() == "BUY" else -order.quantity
        self.positions[order.symbol] = self.positions.get(order.symbol, 0) + signed_qty
        return OrderReceipt(
            broker="simulated",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            submitted_at=datetime.utcnow().isoformat(),
            raw={"positions": dict(self.positions)},
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

    def place_market_order(self, order: OrderRequest) -> OrderReceipt:
        ctx = self._OpenSecTradeContext(filter_trdmarket=self.market, host=self.host, port=self.port, security_firm=self._SecurityFirm.FUTUSG)
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
                submitted_at=datetime.utcnow().isoformat(),
                raw=raw,
            )
        finally:
            ctx.close()


def build_paper_broker(config: dict) -> PaperBroker:
    broker_name = str(config.get("broker", "simulated")).lower()
    if broker_name == "simulated":
        return SimulatedPaperBroker()
    if broker_name == "moomoo":
        return MoomooPaperBroker(
            host=str(config["moomoo_host"]),
            port=int(config["moomoo_port"]),
            market=str(config["moomoo_market"]),
            pwd_unlock=str(config.get("moomoo_pwd_unlock", "")),
        )
    raise ValueError(f"Unsupported paper broker: {broker_name}")
