from __future__ import annotations

from typing import Dict, Optional

from types import Order


class InMemoryOrderStore:
    """Simple in-memory store for orders. In production, replace with a DB."""

    def __init__(self) -> None:
        self._by_token: Dict[str, Order] = {}

    def add(self, order: Order) -> None:
        self._by_token[order.token] = order

    def get_by_token(self, token: str) -> Optional[Order]:
        return self._by_token.get(token)

    def update_status(self, token: str, status: str) -> bool:
        order = self._by_token.get(token)
        if order:
            order.status = status
            return True
        return False
