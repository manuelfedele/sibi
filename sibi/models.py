from dataclasses import dataclass


@dataclass
class OrderStatus:
    orderId: int
    status: str
    filled: float
    remaining: float
    avgFillPrice: float
    permId: int
    parentId: int
    lastFillPrice: float
    clientId: int
    whyHeld: str
    mktCapPrice: float
