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

        # Reset session if user sends greeting at main menu (to restart flow)
        if session.stage == Stage.MAIN_MENU and msg in {"hi", "hello", "habari"}:
            session = self.reset(session)
            self._sessions[session.session_id] = session
            return session.session_id, "LANGUAGE_SELECTION"

        # Handle main menu navigation
        if session.stage == Stage.MAIN_MENU:
            if msg in {"hi", "hello", "habari", "menu", "start", "anza"}:
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
                return session.session_id, "GP_CHAT_INFO"
            if msg in {"2", "2)", "video", "call", "video call", "whatsapp", "gp_video"}:
                return session.session_id, "GP_VIDEO_INFO"
            return session.session_id, "GP_MENU"

        if session.stage == Stage.SPECIALIST:
            if msg in {"1", "1)", "chat", "kuchati", "specialist_chat"}:
                return session.session_id, "SPECIALIST_CHAT_INFO"
            if msg in {"2", "2)", "video", "call", "video call", "specialist_video"}:
                return session.session_id, "SPECIALIST_VIDEO_INFO"
            return session.session_id, "SPECIALIST_MENU"

        if session.stage == Stage.HOME_DOCTOR:
            if msg in {"1", "1)", "quick", "haraka", "matibabu ya haraka"}:
                return session.session_id, "HOME_QUICK_INFO"
            if msg in {"2", "2)", "procedure", "taratibu", "medical procedure"}:
                return session.session_id, "HOME_PROCEDURE_INFO"
            if msg in {"3", "3)", "amd", "mwongozo", "advanced medical directives"}:
                return session.session_id, "HOME_AMD_INFO"
            if msg in {"4", "4)", "sda", "tathmini", "disability assessment"}:
                return session.session_id, "HOME_SDA_INFO"
            return session.session_id, "HOME_DOCTOR_MENU"

        if session.stage == Stage.WORKPLACE:
            if msg in {"1", "1)", "pre", "employment", "pre-employment"}:
                return session.session_id, "WORK_PRE_INFO"
            if msg in {"2", "2)", "screening", "uchunguzi", "health screening"}:
                return session.session_id, "WORK_SCREENING_INFO"
            if msg in {"3", "3)", "wellness", "mada", "workplace wellness"}:
                return session.session_id, "WORK_WELLNESS_INFO"
            return session.session_id, "WORKPLACE_MENU"

        if session.stage == Stage.PHARMACY:
            return session.session_id, "PHARMACY_INFO"

        # Default fallback
        return session.session_id, "MAIN_MENU"
