from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Protocol


@dataclass
class PaymentInitResult:
    token: str
    pay_instructions: str
    checkout_url: str


class PaymentProvider(Protocol):
    def create_checkout(self, *, amount_tzs: int, description: str) -> PaymentInitResult: ...


class DummyPaymentProvider:
    def __init__(self, *, base_checkout_url: str = "https://pay.afyabot.local/checkout") -> None:
        self._base_checkout_url = base_checkout_url.rstrip("/")

    def create_checkout(self, *, amount_tzs: int, description: str) -> PaymentInitResult:
        token = secrets.token_urlsafe(10)
        checkout_url = f"{self._base_checkout_url}/{token}"
        pay_instructions = (
            f"Amount: TZS {amount_tzs}\n"
            f"Service: {description}\n\n"
            "Payment is not integrated yet. For now:\n"
            "1) Copy this token\n"
            "2) Simulate payment by replying: paid <token>\n\n"
            "Later, replace DummyPaymentProvider with M-Pesa/TigoPesa/AirtelMoney/Card gateway."
        )
        return PaymentInitResult(token=token, pay_instructions=pay_instructions, checkout_url=checkout_url)
