from __future__ import annotations

import os
import uuid
from dataclasses import replace
from typing import Dict, Tuple

from afyabot_types import Language, Session, Stage


class AfyabotEngine:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

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

        # Handle initial greeting and language selection
        if session.language is None or session.stage == Stage.LANGUAGE:
            # Only show language selection for initial greeting
            if msg in {"hi", "hello", "habari", "start", "anza"}:
                return session.session_id, "LANGUAGE_SELECTION"
            
            # Handle language choice
            if msg in {"1", "1)", "sw", "swahili", "kiswahili"}:
                session.language = Language.SW
                session.stage = Stage.MAIN_MENU
                return session.session_id, "MAIN_MENU"
            
            if msg in {"2", "2)", "en", "english"}:
                session.language = Language.EN
                session.stage = Stage.MAIN_MENU
                return session.session_id, "MAIN_MENU"
            
            # Invalid choice - show language selection again
            return session.session_id, "LANGUAGE_SELECTION"

        # Reset session if user sends greeting and already has language (to restart flow)
        if session.language is not None and msg in {"hi", "hello", "habari"}:
            session = self.reset(session)
            self._sessions[session.session_id] = session
            return session.session_id, "LANGUAGE_SELECTION"

        # Handle payment collection stages
        if session.stage == Stage.COLLECT_NAME:
            return session.session_id, self._handle_collect_name(session, msg, is_whatsapp)
        
        if session.stage == Stage.COLLECT_PHONE:
            return session.session_id, self._handle_collect_phone(session, msg, is_whatsapp)

        # Handle main menu navigation
        if session.stage == Stage.MAIN_MENU:
            if msg in {"menu", "start", "anza"}:
                return session.session_id, "MAIN_MENU"
            
            if msg in {"1", "1)", "gp", "general", "daktari", "daktari jumla"}:
                session.stage = Stage.GP
                return session.session_id, "GP_MENU"
            
            if msg in {"2", "2)", "specialist", "bingwa", "daktari bingwa"}:
                session.stage = Stage.SPECIALIST
                return session.session_id, "SPECIALIST_MENU"
            
            if msg in {"3", "3)", "home", "home doctor", "daktari nyumbani", "nyumbani"}:
                session.stage = Stage.HOME_DOCTOR
                return session.session_id, "HOME_DOCTOR_MENU"
            
            if msg in {"4", "4)", "corporate", "workplace", "kazini", "mashirika"}:
                session.stage = Stage.WORKPLACE
                return session.session_id, "WORKPLACE_MENU"
            
            if msg in {"5", "5)", "pharmacy", "dawa", "vifaa"}:
                session.stage = Stage.PHARMACY
                return session.session_id, "PHARMACY_MENU"
            
            # Default to main menu for any other input
            return session.session_id, "MAIN_MENU"

        # Handle service-specific menus
        if session.stage == Stage.GP:
            if msg in {"1", "1)", "chat", "kuchati", "gp_chat"}:
                return self._create_checkout(session, "gp_chat", "GP Chat", 3000, "chat", is_whatsapp)
            if msg in {"2", "2)", "video", "call", "video call", "whatsapp", "gp_video"}:
                return self._create_checkout(session, "gp_video", "GP Video", 5000, "video", is_whatsapp)
            return session.session_id, "GP_MENU"

        if session.stage == Stage.SPECIALIST:
            if msg in {"1", "1)", "chat", "kuchati", "specialist_chat"}:
                return self._create_checkout(session, "spec_chat", "Spec Chat", 25000, "chat", is_whatsapp)
            if msg in {"2", "2)", "video", "call", "video call", "specialist_video"}:
                return self._create_checkout(session, "spec_video", "Spec Video", 30000, "video", is_whatsapp)
            return session.session_id, "SPECIALIST_MENU"

        if session.stage == Stage.HOME_DOCTOR:
            if msg in {"1", "1)", "quick", "haraka", "matibabu ya haraka"}:
                return self._create_checkout(session, "home_quick", "Home Quick", 30000, "home", is_whatsapp)
            if msg in {"2", "2)", "procedure", "taratibu", "medical procedure"}:
                return self._create_checkout(session, "home_procedure", "Home Procedure", 30000, "home", is_whatsapp)
            if msg in {"3", "3)", "amd", "mwongozo", "advanced medical directives"}:
                return self._create_checkout(session, "home_amd", "Home AMD", 50000, "home", is_whatsapp)
            if msg in {"4", "4)", "sda", "tathmini", "disability assessment"}:
                return self._create_checkout(session, "home_sda", "Home SDA", 30000, "home", is_whatsapp)
            return session.session_id, "HOME_DOCTOR_MENU"

        if session.stage == Stage.WORKPLACE:
            if msg in {"1", "1)", "pre", "employment", "pre-employment"}:
                return self._create_checkout(session, "work_pre", "Work Pre", 10000, "workplace", is_whatsapp)
            if msg in {"2", "2)", "screening", "uchunguzi", "health screening"}:
                return self._create_checkout(session, "work_screening", "Work Screen", 10000, "workplace", is_whatsapp)
            if msg in {"3", "3)", "wellness", "mada", "workplace wellness"}:
                return self._create_checkout(session, "work_wellness", "Work Wellness", 10000, "workplace", is_whatsapp)
            return session.session_id, "WORKPLACE_MENU"

        if session.stage == Stage.PHARMACY:
            return self._create_checkout(session, "pharmacy_shop", "Pharmacy", 4000, "pharmacy", is_whatsapp)

        # Default fallback
        return session.session_id, "MAIN_MENU"

    def _handle_collect_name(self, session: Session, msg: str, is_whatsapp: bool = False) -> Tuple[str, str]:
        """Handle name collection for payment"""
        name = msg.strip()
        if len(name) < 2:
            if is_whatsapp:
                return session.session_id, "COLLECT_NAME_ERROR"
            return session.session_id, "Jina lako ni fupi sana. Tafadhali andika jina kamili."
        
        session.context["user_name"] = name
        session.stage = Stage.COLLECT_PHONE
        
        if is_whatsapp:
            return session.session_id, "COLLECT_PHONE"
        return session.session_id, "Asante! Sasa andika namba yako ya simu:"

    def _handle_collect_phone(self, session: Session, msg: str, is_whatsapp: bool = False) -> Tuple[str, str]:
        """Handle phone collection for payment"""
        phone = msg.strip()
        # Basic phone validation for Tanzania
        if not (phone.startswith("255") or phone.startswith("0") or phone.startswith("+255")):
            if is_whatsapp:
                return session.session_id, "COLLECT_PHONE_ERROR"
            return session.session_id, "Namba ya simu si sahihi. Tumia namba inaanza na 255, 0, au +255"
        
        session.context["user_phone"] = phone
        
        # Create order summary
        if session.active_order:
            session.active_order.user_name = session.context.get("user_name")
            session.active_order.user_phone = phone
            session.stage = Stage.AWAITING_PAYMENT
            
            if is_whatsapp:
                return session.session_id, "PAYMENT_SUMMARY"
        
        return session.session_id, "Kuna tatizo. Tafadhali jaribu tena."

    def _create_checkout(self, session: Session, service_code: str, service_name: str, amount_tzs: int, channel: str, is_whatsapp: bool = False) -> Tuple[str, str]:
        """Create checkout and start payment flow"""
        # Create simple order (in real app, integrate with payment provider)
        import uuid
        
        order_token = uuid.uuid4().hex[:8]
        
        # Store order info in session
        session.active_order = type('Order', (), {
            'service_code': service_code,
            'service_name': service_name,
            'amount_tzs': amount_tzs,
            'channel': channel,
            'token': order_token,
            'user_name': None,
            'user_phone': None,
            'status': 'pending'
        })()
        
        session.stage = Stage.COLLECT_NAME
        
        if is_whatsapp:
            return session.session_id, "COLLECT_NAME"
        
        return session.session_id, f"Umechagua {service_name}. Bei: TZS {amount_tzs}. Andika jina lako:"
