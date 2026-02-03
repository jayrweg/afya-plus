from __future__ import annotations

import hashlib
import hmac
import json
import os
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from .engine import AfyabotEngine
from .payments_webhook import handle_pesapal_webhook
from .whatsapp_cloud import send_whatsapp_text, send_whatsapp_buttons, send_whatsapp_list

load_dotenv()

_ENGINE = AfyabotEngine()


def verify_webhook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify X-Hub-Signature-256 from Facebook"""
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        app_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature[7:], expected_signature)


class AfyabotHandler(BaseHTTPRequestHandler):
    server_version = "AfyabotHTTP/1.0"

    def _send(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        print(f"[DEBUG] GET path: '{path}'")

        if path in {"", "health"}:
            self._send(200, {"ok": True, "service": "afyabot"})
            return

        if path == "/whatsapp/webhook":
            verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
            qs = parse_qs(parsed.query)
            mode = (qs.get("hub.mode", [""])[0] or "").strip()
            token = (qs.get("hub.verify_token", [""])[0] or "").strip()
            challenge = (qs.get("hub.challenge", [""])[0] or "").strip()

            if mode == "subscribe" and token and verify_token and token == verify_token:
                body = (challenge or "").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self._send(403, {"ok": False, "error": "verification_failed"})
            return

        # Serve static test UI
        if path == "/test_ui.html":
            try:
                ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_ui.html"))
                print(f"[DEBUG] Serving test_ui.html from: {ui_path}")
                with open(ui_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return
            except Exception as e:
                print(f"[ERROR] Failed to serve test_ui.html: {e}")
                self._send(500, {"ok": False, "error": "file_not_found"})
                return

        self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/")

        if path == "/chat":
            self._handle_chat_post()
            return

        if path == "/whatsapp/webhook":
            self._handle_whatsapp_webhook_post()
            return

        if path == "/payments/pesapal":
            self._handle_pesapal_webhook_post()
            return

        self._send(404, {"ok": False, "error": "not_found"})
        return

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b""
        return json.loads(raw.decode("utf-8") or "{}")

    def _handle_chat_post(self) -> None:
        try:
            data = self._read_json()
        except Exception:
            self._send(400, {"ok": False, "error": "invalid_json"})
            return

        session_id = data.get("session_id")
        message = data.get("message", "")
        sid, reply = _ENGINE.handle_message(session_id=session_id, text=str(message))
        self._send(200, {"ok": True, "session_id": sid, "reply": reply})

    def _handle_whatsapp_webhook_post(self) -> None:
        try:
            # Get raw payload for signature verification
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw_payload = self.rfile.read(length) if length > 0 else b""
            
            # Verify webhook signature (optional but recommended)
            app_secret = os.getenv("FACEBOOK_APP_SECRET", "")
            signature = self.headers.get("X-Hub-Signature-256", "")
            
            if app_secret and signature:
                if not verify_webhook_signature(raw_payload, signature, app_secret):
                    print("[WARNING] Webhook signature verification failed")
                    # Still process the webhook for testing, but log the warning
            
            # Parse JSON payload
            try:
                data = json.loads(raw_payload.decode("utf-8") or "{}")
            except Exception as e:
                print(f"[ERROR] Failed to parse webhook JSON: {e}")
                self._send(400, {"ok": False, "error": "invalid_json"})
                return

            entry = (data.get("entry") or [])[0] or {}
            changes = (entry.get("changes") or [])[0] or {}
            value = changes.get("value") or {}
            messages = value.get("messages") or []
            if not messages:
                self._send(200, {"ok": True, "status": "no_messages"})
                return

            message_obj = messages[0] or {}
            from_number = str(message_obj.get("from") or "").strip()
            phone_number_id = str((value.get("metadata") or {}).get("phone_number_id") or "").strip()

            text = ""
            interactive = message_obj.get("interactive") or {}
            if isinstance(interactive, dict) and "button_reply" in interactive:
                text = str((interactive.get("button_reply") or {}).get("id") or "")
            elif isinstance(interactive, dict) and "list_reply" in interactive:
                text = str((interactive.get("list_reply") or {}).get("id") or "")
            else:
                text = str((message_obj.get("text") or {}).get("body") or "")

            session_id = from_number or None
            sid, reply = _ENGINE.handle_message(session_id=session_id, text=text, is_whatsapp=True)

            # Handle special WhatsApp responses
            if reply == "LANGUAGE_SELECTION":
                self._send_language_selection(phone_number_id, from_number)
            elif reply == "MAIN_MENU":
                self._send_main_menu(phone_number_id, from_number)
            elif reply == "GP_OPTIONS":
                self._send_gp_options(phone_number_id, from_number)
            elif reply == "SPECIALIST_OPTIONS":
                self._send_specialist_options(phone_number_id, from_number)
            elif reply == "HOME_DOCTOR_MENU":
                self._send_home_doctor_menu(phone_number_id, from_number)
            elif reply == "WORKPLACE_MENU":
                self._send_workplace_menu(phone_number_id, from_number)
            elif reply == "PHARMACY_MENU":
                self._send_pharmacy_menu(phone_number_id, from_number)
            elif phone_number_id and from_number:
                send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=reply)

            self._send(200, {"ok": True, "session_id": sid})

        except Exception:
            self._send(200, {"ok": True, "status": "ignored"})

    def _send_language_selection(self, phone_number_id: str, to: str) -> None:
        message = "Afyabot (Afya+)\nHabari! Karibu Afya+. Chaguo bora kwa afya yako.\n\nChagua lugha:"
        buttons = [
            {"id": "1", "title": "Kiswahili"},
            {"id": "2", "title": "English"}
        ]
        send_whatsapp_buttons(phone_number_id=phone_number_id, to=to, message=message, buttons=buttons)

    def _send_main_menu(self, phone_number_id: str, to: str) -> None:
        message = "Afyaplus inakuletea huduma zifuatazo, chagua:\n\nKumbuka: Afyabot hatoi utambuzi rasmi wa ugonjwa. Kwa dharura piga simu huduma ya dharura ya eneo lako mara moja."
        sections = [{
            "title": "Afyabot Services",
            "rows": [
                {"id": "1", "title": "🩺 Kuwasiliana na daktari jumla (GP)", "description": "Ushauri na matibabu ya magonjwa ya kawaida"},
                {"id": "2", "title": "👨‍⚕️ Kuwasiliana na daktari bingwa (Specialist)", "description": "Daktari bingwa kwa huduma maalum"},
                {"id": "3", "title": "🏠 Huduma ya daktari nyumbani (Home Doctor)", "description": "Daktari anakuja nyumbani kwako"},
                {"id": "4", "title": "🏢 Afya mazingira ya kazi (Corporate)", "description": "Huduma za afya kwa wafanyakazi"},
                {"id": "5", "title": "💊 Ushauri/maelekezo ya dawa (Pharmacy)", "description": "Dawa na vifaa tiba"}
            ]
        }]
        send_whatsapp_list(phone_number_id=phone_number_id, to=to, message=message, sections=sections)

    def _send_gp_options(self, phone_number_id: str, to: str) -> None:
        message = "Afya+ inakuunganisha na daktari kwa ushauri na matibabu papo hapo.\n\nHusaidia magonjwa ya kawaida na sugu kama: chunusi/eczema, mzio, wasiwasi, pumu, maumivu ya mgongo, uzazi wa mpango, mafua/homa/kikohozi, kisukari, UTI n.k.\n\nChagua njia ya huduma:"
        buttons = [
            {"id": "1", "title": "💬 Kuchati kwenye simu (TZS 100)"},
            {"id": "2", "title": "📹 WhatsApp video call (TZS 200)"}
        ]
        send_whatsapp_buttons(phone_number_id=phone_number_id, to=to, message=message, buttons=buttons)

    def _send_specialist_options(self, phone_number_id: str, to: str) -> None:
        message = "Afya+ inakuletea daktari bingwa kwa ushauri wa kitaalamu (ngozi, uzazi/wanawake, watoto, moyo/presha/sukari, mifupa, mmeng'enyo n.k.).\n\nChagua njia:"
        buttons = [
            {"id": "1", "title": "💬 Kuchati (TZS 300)"},
            {"id": "2", "title": "📹 Video call (TZS 300)"}
        ]
        send_whatsapp_buttons(phone_number_id=phone_number_id, to=to, message=message, buttons=buttons)

    def _send_home_doctor_menu(self, phone_number_id: str, to: str) -> None:
        message = "Huduma ya daktari nyumbani. Chagua:"
        sections = [{
            "title": "Home Doctor Services",
            "rows": [
                {"id": "1", "title": "⚡ Matibabu ya haraka", "description": "TZS 300"},
                {"id": "2", "title": "🔧 Taratibu tiba / Medical procedure", "description": "TZS 300"},
                {"id": "3", "title": "📋 Mwongozo wa matibabu (AMD)", "description": "TZS 300"},
                {"id": "4", "title": "♿ Tathmini ya ulemavu (SDA)", "description": "TZS 300"}
            ]
        }]
        send_whatsapp_list(phone_number_id=phone_number_id, to=to, message=message, sections=sections)

    def _send_workplace_menu(self, phone_number_id: str, to: str) -> None:
        message = "Afya mazingira ya kazi. Chagua:"
        sections = [{
            "title": "Corporate Services",
            "rows": [
                {"id": "1", "title": "📋 Pre-employment medical check", "description": "TZS 200"},
                {"id": "2", "title": "🔬 Health screening & vaccination", "description": "TZS 200"},
                {"id": "3", "title": "💼 Workplace wellness solutions", "description": "TZS 200"}
            ]
        }]
        send_whatsapp_list(phone_number_id=phone_number_id, to=to, message=message, sections=sections)

    def _send_pharmacy_menu(self, phone_number_id: str, to: str) -> None:
        message = "Pharmacy: Shop health and wellness (TZS 100)."
        buttons = [
            {"id": "1", "title": "🛒 Continue to shop"}
        ]
        send_whatsapp_buttons(phone_number_id=phone_number_id, to=to, message=message, buttons=buttons)

    def _handle_pesapal_webhook_post(self) -> None:
        try:
            data = self._read_json()
        except Exception:
            self._send(400, {"ok": False, "error": "invalid_json"})
            return

        result = handle_pesapal_webhook(data, store=_ENGINE.store, sessions=_ENGINE.sessions)
        if result.get("ok"):
            self._send(200, {"ok": True, "order_id": result.get("order_id"), "status": result.get("status")})
        else:
            self._send(400, {"ok": False, "error": result.get("error", "webhook_failed")})


def run(*, host: str = "127.0.0.1", port: int = 8008) -> None:
    import os
    httpd = HTTPServer((host, port), AfyabotHandler)
    print(f"Afyabot server running on http://{host}:{port}")
    print("POST /chat  {session_id?, message}")
    print("GET/POST /whatsapp/webhook  (WhatsApp Cloud API)")
    print("POST /payments/pesapal  (Pesapal IPN webhook)")
    print(f"Test UI: http://{host}:{port}/test_ui.html")
    httpd.serve_forever()


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8008"))
    run(host=host, port=port)
