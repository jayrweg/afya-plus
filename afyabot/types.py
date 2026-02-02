from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid

class Language(Enum):
    EN = "en"
    SW = "sw"

class Stage(Enum):
    START = "start"
    LANGUAGE = "language"
    MAIN_MENU = "menu"
    GP = "gp"
    SPECIALIST = "specialist"
    HOME_DOCTOR = "home_doctor"
    WORKPLACE = "workplace"
    PHARMACY = "pharmacy"
    COLLECT_NAME = "collect_name"
    COLLECT_PHONE = "collect_phone"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"

@dataclass
class Order:
    service_code: str
    service_name: str
    amount_tzs: int
    channel: str
    token: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
    user_name: Optional[str] = None
    user_phone: Optional[str] = None

@dataclass
class Session:
    session_id: str
    language: Language = Language.EN
    stage: Stage = Stage.START
    active_order: Optional[Order] = None
    context: dict = field(default_factory=dict)
