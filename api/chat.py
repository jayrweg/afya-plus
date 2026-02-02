import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing engine
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from afyabot.engine import AfyabotEngine

_ENGINE = AfyabotEngine()

def handler(request):
    """Vercel serverless function for chat endpoint"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            session_id = data.get("session_id")
            message = data.get("message", "")
            sid, reply = _ENGINE.handle_message(session_id=session_id, text=str(message))
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                },
                'body': json.dumps({"ok": True, "session_id": sid, "reply": reply})
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
