import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Import your existing engine and WhatsApp functions
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from afyabot.engine import AfyabotEngine
from afyabot.whatsapp_cloud import send_whatsapp_text, send_whatsapp_buttons, send_whatsapp_list

_ENGINE = AfyabotEngine()

def handler(request):
    """Vercel serverless function for WhatsApp webhook"""
    try:
        if request.method == 'GET':
            # Handle webhook verification
            query = request.args
            mode = query.get('hub.mode', '')
            token = query.get('hub.verify_token', '')
            challenge = query.get('hub.challenge', '')
            verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
            
            print(f"[DEBUG] Webhook verification:")
            print(f"  Mode: {mode}")
            print(f"  Token: {token}")
            print(f"  Expected: {verify_token}")
            print(f"  Challenge: {challenge}")
            
            if mode == 'subscribe' and token and verify_token and token == verify_token:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'text/plain'},
                    'body': challenge
                }
            else:
                return {
                    'statusCode': 403,
                    'body': 'Verification failed'
                }
        
        elif request.method == 'POST':
            # Handle incoming WhatsApp messages
            data = request.get_json()
            
            entry = (data.get("entry") or [])[0] or {}
            changes = (entry.get("changes") or [])[0] or {}
            value = changes.get("value") or {}
            messages = value.get("messages") or []
            
            if not messages:
                return {
                    'statusCode': 200,
                    'body': json.dumps({"ok": True, "status": "no_messages"})
                }
            
            message_obj = messages[0] or {}
            from_number = str(message_obj.get("from") or "").strip()
            phone_number_id = str((value.get("metadata") or {}).get("phone_number_id") or "").strip()
            
            # Extract message text
            text = ""
            interactive = message_obj.get("interactive") or {}
            if isinstance(interactive, dict) and "button_reply" in interactive:
                text = str((interactive.get("button_reply") or {}).get("id") or "")
            elif isinstance(interactive, dict) and "list_reply" in interactive:
                text = str((interactive.get("list_reply") or {}).get("id") or "")
            else:
                text = str((message_obj.get("text") or {}).get("body") or "")
            
            # Process message
            session_id = from_number or None
            sid, reply = _ENGINE.handle_message(session_id=session_id, text=text, is_whatsapp=True)
            
            # Handle special WhatsApp responses
            if reply == "LANGUAGE_SELECTION":
                # Send language buttons
                message = "Afyabot (Afya+)\nHabari! Karibu Afya+. Chaguo bora kwa afya yako.\n\nChagua lugha:"
                buttons = [
                    {"id": "1", "title": "Kiswahili"},
                    {"id": "2", "title": "English"}
                ]
                send_whatsapp_buttons(phone_number_id=phone_number_id, to=from_number, message=message, buttons=buttons)
            elif reply == "MAIN_MENU":
                # Send main menu list
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
                send_whatsapp_list(phone_number_id=phone_number_id, to=from_number, message=message, sections=sections)
            elif phone_number_id and from_number:
                send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=reply)
            
            return {
                'statusCode': 200,
                'body': json.dumps({"ok": True, "session_id": sid})
            }
        
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({"error": "Method not allowed"})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }
