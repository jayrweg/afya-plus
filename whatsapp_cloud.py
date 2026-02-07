from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List, Optional


def send_whatsapp_text(*, phone_number_id: str, to: str, message: str) -> Optional[Dict[str, Any]]:
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    api_version = os.getenv("WHATSAPP_API_VERSION", "v19.0")

    if not access_token:
        return None

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except Exception:
                return {"raw": raw, "status": resp.status}
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return None


def send_whatsapp_buttons(*, phone_number_id: str, to: str, message: str, buttons: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """Send interactive buttons message"""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    api_version = os.getenv("WHATSAPP_API_VERSION", "v19.0")

    if not access_token:
        return None

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    # Format buttons for WhatsApp API
    button_objects = []
    for i, button in enumerate(buttons[:3], 1):  # WhatsApp supports max 3 buttons
        button_objects.append({
            "type": "reply",
            "reply": {
                "id": button.get("id", str(i)),
                "title": button.get("title", f"Option {i}")
            }
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": message},
            "action": {
                "buttons": button_objects
            }
        }
    }

    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except Exception:
                return {"raw": raw, "status": resp.status}
    except Exception as e:
        print(f"Error sending WhatsApp buttons: {e}")
        return None


def send_whatsapp_list(
    phone_number_id: str, 
    to: str, 
    message: str, 
    sections: list[dict[str, any]], 
    button_text: str = "Options"
) -> dict[str, any]:
    """Send interactive list message"""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    api_version = os.getenv("WHATSAPP_API_VERSION", "v19.0")

    if not access_token:
        return None

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    # Format sections for WhatsApp API
    section_objects = []
    for section in sections[:10]:  # WhatsApp supports max 10 sections
        rows = []
        for row in section.get("rows", [])[:10]:  # Max 10 rows per section
            rows.append({
                "id": row.get("id", ""),
                "title": row.get("title", ""),
                "description": row.get("description", "")
            })
        
        section_objects.append({
            "title": section.get("title", ""),
            "rows": rows
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": message},
            "action": {
                "button": button_text,
                "sections": section_objects
            }
        }
    }

    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except Exception:
                return {"raw": raw, "status": resp.status}
    except Exception as e:
        print(f"Error sending WhatsApp list: {e}")
        return None
