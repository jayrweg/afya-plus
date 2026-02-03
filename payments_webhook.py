from __future__ import annotations

import json
import os
from typing import Any, Dict

from .email_sender import send_payment_confirmation_email
from .order_store import InMemoryOrderStore
from .pesapal_provider import PesapalPaymentProvider, PesapalConfig
from .types import Session


def handle_pesapal_webhook(payload: Dict[str, Any], store: InMemoryOrderStore, sessions: Dict[str, Session]) -> Dict[str, Any]:
    """
    Handle Pesapal IPN (instant payment notification).
    Expected payload includes: order_tracking_id, status, etc.
    """
    order_id = payload.get("order_tracking_id")
    status = payload.get("status", "").lower()

    if not order_id:
        return {"ok": False, "error": "missing_order_id"}

    order = store.get_by_token(order_id)
    if not order:
        return {"ok": False, "error": "order_not_found"}

    # Update order status
    store.update_status(order_id, status)

    # Find the session by phone (session_id == phone)
    session = sessions.get(order.token)  # In our simple flow, token == session_id; adjust if needed
    if not session:
        # fallback: try matching by active_order token
        for s in sessions.values():
            if s.active_order and s.active_order.token == order_id:
                session = s
                break

    if status == "completed":
        # Email admin with full details
        admin_email = os.getenv("RESEND_ADMIN_EMAIL")
        if admin_email and session:
            send_payment_confirmation_email(admin_email, session, order)

        # Mark session order as paid
        if session and session.active_order:
            session.active_order.status = "paid"

    return {"ok": True, "order_id": order_id, "status": status}
