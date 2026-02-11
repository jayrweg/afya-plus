import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Import WhatsApp functions
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from afyabot.whatsapp_cloud import send_whatsapp_text, send_whatsapp_buttons, send_whatsapp_list

def handler(request):
    """Simple Valentine's test bot"""
    try:
        if request.method == 'GET':
            # Handle webhook verification
            query = request.args
            mode = query.get('hub.mode', '')
            token = query.get('hub.verify_token', '')
            challenge = query.get('hub.challenge', '')
            verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
            
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
                text = str((message_obj.get("text") or {}).get("body") or "").lower()
            
            # Simple Valentine's bot logic
            if text in ["hi", "hello", "habari", "helo"]:
                header = "Valentine's Special"
                body = "Choose a gift for your loved one:"
                footer = "Make this Valentine's special"
                sections = [{
                    "title": "Gift Options",
                    "rows": [
                        {
                            "id": "1",
                            "title": "Roses",
                            "description": "Fresh red roses bouquet"
                        },
                        {
                            "id": "2",
                            "title": "Chocolate Box",
                            "description": "Premium chocolate selection"
                        },
                        {
                            "id": "3",
                            "title": "Love Letter",
                            "description": "Personalized romantic message"
                        },
                        {
                            "id": "4",
                            "title": "Dinner Reservation",
                            "description": "Romantic restaurant booking"
                        }
                    ]
                }]
                button_text = "Choose gift"
                send_whatsapp_list(phone_number_id=phone_number_id, to=from_number, header=header, body=body, footer=footer, sections=sections, button_text=button_text)
            
            elif text in ["1", "2", "3", "4"]:
                gifts = {
                    "1": "Roses - Beautiful red roses that express your love perfectly!",
                    "2": "Chocolate Box - Premium chocolates for sweet moments together!",
                    "3": "Love Letter - Words from the heart that last forever!",
                    "4": "Dinner Reservation - Romantic dinner for two under the stars!"
                }
                message = gifts.get(text, "Choose a gift option from the menu")
                send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            
            else:
                message = "Happy Valentine's Day! Say 'hi' to see gift options."
                send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            
            return {
                'statusCode': 200,
                'body': json.dumps({"ok": True})
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
