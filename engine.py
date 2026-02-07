from __future__ import annotations

import os
import re
import uuid
from dataclasses import replace
from typing import Dict, Tuple

from catalog import t
from order_store import InMemoryOrderStore
from payments import DummyPaymentProvider
from pesapal_provider import PesapalPaymentProvider, PesapalConfig
from afyabot_types import Language, Order, Session, Stage


class AfyabotEngine:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._store = InMemoryOrderStore()
        # Choose payment provider based on env
        if os.getenv("PESAPAL_CONSUMER_KEY") and os.getenv("PESAPAL_CONSUMER_SECRET"):
            cfg = PesapalConfig(
                consumer_key=os.getenv("PESAPAL_CONSUMER_KEY"),
                consumer_secret=os.getenv("PESAPAL_CONSUMER_SECRET"),
                ipn_url=os.getenv("PESAPAL_IPN_URL", ""),
            )
            self._payments = PesapalPaymentProvider(cfg)
        else:
            self._payments = DummyPaymentProvider()

    @property
    def store(self) -> InMemoryOrderStore:
        return self._store

    @property
    def sessions(self) -> Dict[str, Session]:
        return self._sessions

    def get_or_create_session(self, session_id: str | None) -> Session:
        if not session_id:
            session_id = uuid.uuid4().hex
        sess = self._sessions.get(session_id)
        if sess is None:
            sess = Session(session_id=session_id)
            self._sessions[session_id] = sess
        return sess

    def reset(self, session: Session) -> Session:
        return replace(session, language=None, stage=Stage.LANGUAGE, context={}, active_order=None)

    def handle_message(self, *, session_id: str | None, text: str, is_whatsapp: bool = False) -> Tuple[str, str]:
        session = self.get_or_create_session(session_id)
        raw = (text or "").strip()
        msg = raw.lower()

        # Handle "hi" in any state when no language is set
        if msg in {"hi", "hello", "habari"} and session.language is None:
            return session.session_id, self._render_language_prompt(session, is_whatsapp)

        if msg in {"start", "restart", "upya"}:
            session = self.reset(session)
            self._sessions[session.session_id] = session
            return session.session_id, self._render_language_prompt(session, is_whatsapp)

        if msg in {"menu", "mwanzo", "home"} and session.language is not None:
            session.stage = Stage.MAIN_MENU
            session.active_order = None
            return session.session_id, self._render_main_menu(session, is_whatsapp)

        if session.language is None or session.stage == Stage.LANGUAGE:
            reply, new_lang = self._handle_language_choice(msg)
            if new_lang is None:
                return session.session_id, reply
            session.language = new_lang
            session.stage = Stage.MAIN_MENU
            return session.session_id, self._render_main_menu(session, is_whatsapp)

        if msg.startswith("paid"):
            return session.session_id, self._handle_paid(session, raw)

        if session.stage == Stage.MAIN_MENU:
            return session.session_id, self._handle_main_menu(session, msg, is_whatsapp)

        if session.stage == Stage.GP:
            return session.session_id, self._handle_gp(session, msg, is_whatsapp)

        if session.stage == Stage.SPECIALIST:
            return session.session_id, self._handle_specialist(session, msg, is_whatsapp)

        if session.stage == Stage.HOME_DOCTOR:
            return session.session_id, self._handle_home_doctor(session, msg, is_whatsapp)

        if session.stage == Stage.WORKPLACE:
            return session.session_id, self._handle_workplace(session, msg, is_whatsapp)

        if session.stage == Stage.PHARMACY:
            return session.session_id, self._handle_pharmacy(session, msg, is_whatsapp)

        if session.stage == Stage.COLLECT_NAME:
            return session.session_id, self._handle_collect_name(session, msg)

        if session.stage == Stage.COLLECT_PHONE:
            return session.session_id, self._handle_collect_phone(session, msg)

        return session.session_id, t(session.language, "fallback")

    def _render_language_prompt(self, session: Session, is_whatsapp: bool = False) -> str:
        if is_whatsapp:
            # For WhatsApp, we'll use buttons
            return "LANGUAGE_SELECTION"  # Special marker for WhatsApp handler
        return "\n".join([
            "Afyabot (Afya+)",
            t(Language.SW, "greeting"),
            t(Language.SW, "choose_language"),
        ])

    def _render_main_menu(self, session: Session, is_whatsapp: bool = False) -> str:
        if is_whatsapp:
            return "MAIN_MENU"  # Special marker for WhatsApp handler
        return "\n\n".join([
            t(session.language, "main_menu"),
            t(session.language, "disclaimer"),
        ])

    def _handle_language_choice(self, msg: str) -> Tuple[str, Language | None]:
        if msg in {"", "hi", "hello", "habari", "start", "anza", "menu"}:
            return "\n".join([
                "Afyabot (Afya+)",
                t(Language.SW, "greeting"),
                t(Language.SW, "choose_language"),
            ]), None
        if msg in {"1", "1)", "sw", "swahili", "kiswahili"}:
            return "\n".join([
                t(Language.SW, "greeting"),
                t(Language.SW, "choose_language"),
            ]), Language.SW
        if msg in {"2", "2)", "en", "english"}:
            return "\n".join([
                t(Language.EN, "greeting"),
                t(Language.EN, "choose_language"),
            ]), Language.EN
        return "\n\n".join([
            t(Language.SW, "invalid_language"),
            t(Language.SW, "choose_language"),
        ]), None

    def _handle_main_menu(self, session: Session, msg: str, is_whatsapp: bool = False) -> str:
        if msg in {"1", "1)", "gp", "general", "daktari", "daktari jumla"}:
            session.stage = Stage.GP
            if is_whatsapp:
                return "GP_MENU"
            return "\n\n".join([t(session.language, "gp_info"), t(session.language, "gp_channel")])

        if msg in {"2", "2)", "specialist", "bingwa", "daktari bingwa"}:
            session.stage = Stage.SPECIALIST
            if is_whatsapp:
                return "SPECIALIST_MENU"
            return "\n\n".join([t(session.language, "specialist_info"), t(session.language, "specialist_channel")])

        if msg in {"3", "3)", "home", "home doctor", "daktari nyumbani", "nyumbani"}:
            session.stage = Stage.HOME_DOCTOR
            if is_whatsapp:
                return "HOME_DOCTOR_MENU"
            return t(session.language, "home_doctor_menu")

        if msg in {"4", "4)", "corporate", "workplace", "kazini", "mashirika"}:
            session.stage = Stage.WORKPLACE
            if is_whatsapp:
                return "WORKPLACE_MENU"
            return t(session.language, "workplace_menu")

        if msg in {"5", "5)", "pharmacy", "dawa", "vifaa"}:
            session.stage = Stage.PHARMACY
            if is_whatsapp:
                return "PHARMACY_MENU"
            return t(session.language, "pharmacy_menu")

        return t(session.language, "fallback")

    def _handle_gp(self, session: Session, msg: str, is_whatsapp: bool = False) -> str:
        if msg in {"1", "1)", "chat", "kuchati", "gp_chat"}:
            return self._create_checkout(session, service_code="gp_chat", service_name="GP Chat", amount_tzs=100, channel="chat")
        if msg in {"2", "2)", "video", "call", "video call", "whatsapp", "gp_video"}:
            return self._create_checkout(session, service_code="gp_video", service_name="GP Video", amount_tzs=200, channel="video")
        return t(session.language, "gp_channel")

    def _handle_specialist(self, session: Session, msg: str, is_whatsapp: bool = False) -> str:
        if msg in {"1", "1)", "chat", "kuchati", "specialist_chat"}:
            return self._create_checkout(session, service_code="spec_chat", service_name="Specialist Chat", amount_tzs=300, channel="chat")
        if msg in {"2", "2)", "video", "call", "video call", "specialist_video"}:
            return self._create_checkout(session, service_code="spec_video", service_name="Specialist Video", amount_tzs=300, channel="video")
        return t(session.language, "specialist_channel")

    def _handle_home_doctor(self, session: Session, msg: str, is_whatsapp: bool = False) -> str:
        mapping = {
            "1": ("home_quick", "Home Doctor - Quick treatment", 300),
            "2": ("home_procedure", "Home Doctor - Medical procedure", 300),
            "3": ("home_amd", "Home Doctor - AMD", 300),
            "4": ("home_sda", "Home Doctor - SDA", 300),
        }
        for key, val in mapping.items():
            if msg in {key, f"{key})"}:
                code, name, amt = val
                return self._create_checkout(session, service_code=code, service_name=name, amount_tzs=amt, channel="home")
        return t(session.language, "home_doctor_menu")

    def _handle_workplace(self, session: Session, msg: str, is_whatsapp: bool = False) -> str:
        mapping = {
            "1": ("work_pre_employment", "Pre-employment medical check", 200),
            "2": ("work_screening", "Health screening & vaccination", 200),
            "3": ("work_wellness", "Workplace wellness solutions", 200),
        }
        for key, val in mapping.items():
            if msg in {key, f"{key})"}:
                code, name, amt = val
                return self._create_checkout(session, service_code=code, service_name=name, amount_tzs=amt, channel="workplace")
        return t(session.language, "workplace_menu")

    def _handle_pharmacy(self, session: Session, msg: str, is_whatsapp: bool = False) -> str:
        if msg in {"1", "1)", "shop", "nunua", "endelea"}:
            return self._create_checkout(session, service_code="pharmacy_shop", service_name="Pharmacy", amount_tzs=100, channel="shop")
        return t(session.language, "pharmacy_menu") + "\n" + "Type 1 to continue, or 'menu' to go back."

    def _handle_collect_name(self, session: Session, msg: str) -> str:
        session.context["user_name"] = msg.strip()
        session.stage = Stage.COLLECT_PHONE
        return t(session.language, "ask_phone")

    def _handle_collect_phone(self, session: Session, msg: str) -> str:
        session.context["user_phone"] = msg.strip()
        session.active_order.user_name = session.context.get("user_name")
        session.active_order.user_phone = session.context.get("user_phone")
        session.stage = Stage.AWAITING_PAYMENT
        lines = [t(session.language, "checkout_created")]
        lines.append(f"Amount: TZS {session.active_order.amount_tzs}")
        lines.append(f"Service: {session.active_order.service_name}")
        lines.append(f"Name: {session.active_order.user_name}")
        lines.append(f"Phone: {session.active_order.user_phone}")
        result = session.context.get("payment_result")
        if result and result.checkout_url:
            lines.append(f"Pay: {result.checkout_url}")
        else:
            lines.append("Payment is not integrated (demo).")
        lines.append("")
        lines.append("After payment, type: paid " + session.active_order.token)
        return "\n".join(lines)

    def _create_checkout(self, session: Session, *, service_code: str, service_name: str, amount_tzs: int, channel: str) -> str:
        description = service_name
        result = self._payments.create_checkout(amount_tzs=amount_tzs, description=description)
        order = Order(
            service_code=service_code,
            service_name=service_name,
            amount_tzs=amount_tzs,
            channel=channel,
            token=result.token,
            status="pending",
        )
        session.active_order = order
        self._store.add(order)
        # Store payment result for later use
        session.context["payment_result"] = result
        session.stage = Stage.COLLECT_NAME
        lines = [t(session.language, "checkout_created")]
        lines.append(f"Amount: TZS {amount_tzs}")
        lines.append(f"Service: {service_name}")
        lines.append("")
        lines.append(t(session.language, "ask_name"))
        return "\n".join(lines)

    def _handle_paid(self, session: Session, raw: str) -> str:
        if session.active_order is None:
            return t(session.language, "paid_invalid")

        m = re.match(r"^paid\s+(.+)$", raw.strip(), flags=re.IGNORECASE)
        if not m:
            return t(session.language, "paid_invalid")

        token = m.group(1).strip()
        if token != session.active_order.token:
            return t(session.language, "paid_invalid")

        session.active_order.status = "paid"
        session.stage = Stage.MAIN_MENU
        return "\n\n".join([
            t(session.language, "paid_ok"),
            self._render_main_menu(session),
        ])
