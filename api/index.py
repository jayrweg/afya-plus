from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
import json
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Add afyabot to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing engine and WhatsApp functions
from engine import AfyabotEngine
from whatsapp_cloud import send_whatsapp_text, send_whatsapp_buttons, send_whatsapp_list

app = FastAPI(title="Afyabot Health Chatbot")

_ENGINE = AfyabotEngine()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "afyabot-fastapi"}

@app.get("/")
async def root():
    """Serve the main UI"""
    try:
        # Try different possible paths for the HTML file
        possible_paths = [
            'public/index.html',
            '../public/index.html',
            '/var/task/public/index.html',
            '/vercel/path0/public/index.html'
        ]
        
        content = None
        for path in possible_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                break
            except FileNotFoundError:
                continue
        
        if content:
            return HTMLResponse(content=content)
        else:
            # Fallback: simple HTML interface
            return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Afyabot - Health Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
        input, button { padding: 10px; margin: 5px; }
        #messages { max-height: 400px; overflow-y: auto; border: 1px solid #eee; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Afyabot - Health Chatbot</h1>
    <div class="chat-container">
        <div id="messages"></div>
        <div>
            <input type="text" id="messageInput" placeholder="Type your message..." style="width: 70%;">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const messages = document.getElementById('messages');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            messages.innerHTML += '<p><strong>You:</strong> ' + message + '</p>';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message, session_id: 'web-user' })
                });
                
                const data = await response.json();
                messages.innerHTML += '<p><strong>Afyabot:</strong> ' + data.reply + '</p>';
            } catch (error) {
                messages.innerHTML += '<p><strong>Error:</strong> ' + error.message + '</p>';
            }
            
            input.value = '';
            messages.scrollTop = messages.scrollHeight;
        }
        
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
            """)
    except Exception as e:
        return HTMLResponse(f"<h1>Afyabot</h1><p>Error: {str(e)}</p>", status_code=500)

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Chat API endpoint"""
    try:
        data = await request.json()
        session_id = data.get("session_id")
        message = data.get("message", "")
        sid, reply = _ENGINE.handle_message(session_id=session_id, text=str(message))
        
        return JSONResponse({
            "ok": True, 
            "session_id": sid, 
            "reply": reply
        })
    except Exception as e:
        return JSONResponse({
            "ok": False, 
            "error": str(e)
        }, status_code=500)

@app.get("/api/whatsapp/webhook")
async def whatsapp_webhook_get(request: Request):
    """WhatsApp webhook verification"""
    # Log the incoming verification request for debugging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    mode = request.query_params.get('hub.mode', '')
    token = request.query_params.get('hub.verify_token', '')
    challenge = request.query_params.get('hub.challenge', '')
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    
    logger.info("=== WHATSAPP WEBHOOK VERIFICATION REQUEST ===")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Query params: {dict(request.query_params)}")
    logger.info(f"Mode: '{mode}'")
    logger.info(f"Token from Facebook: '{token}'")
    logger.info(f"Expected verify token: '{verify_token}'")
    logger.info(f"Challenge: '{challenge}'")
    
    if mode == 'subscribe' and token and verify_token and token == verify_token:
        logger.info("✅ WEBHOOK VERIFICATION SUCCESSFUL")
        logger.info(f"Returning challenge: {challenge}")
        return PlainTextResponse(content=challenge)
    else:
        logger.error("❌ WEBHOOK VERIFICATION FAILED")
        logger.error(f"Mode check: {mode == 'subscribe'}")
        logger.error(f"Token check: {token == verify_token}")
        logger.error(f"Token provided: '{token}'")
        logger.error(f"Token expected: '{verify_token}'")
        return PlainTextResponse(content="Verification failed", status_code=403)

@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook_post(request: Request):
    """WhatsApp webhook message handling"""
    try:
        # Log the incoming request for debugging
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        logger.info("=== WHATSAPP WEBHOOK POST REQUEST ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Get raw body for signature verification
        body = await request.body()
        logger.info(f"Raw body: {body.decode('utf-8', errors='replace')}")
        
        logger.info("WhatsApp webhook POST received")
        
        data = await request.json()
        logger.info(f"Webhook data: {data}")
        
        entry = (data.get("entry") or [])[0] or {}
        changes = (entry.get("changes") or [])[0] or {}
        value = changes.get("value") or {}
        messages = value.get("messages") or []
        
        logger.info(f"Messages found: {len(messages)}")
        
        if not messages:
            logger.info("No messages in webhook - this might be a health check or other event")
            # Log what we did get in the webhook
            logger.info(f"Webhook contains: {list(data.keys())}")
            if 'entry' in data:
                logger.info(f"Entry data: {data['entry']}")
            return JSONResponse({"ok": True, "status": "no_messages"})
        
        message_obj = messages[0] or {}
        from_number = str(message_obj.get("from") or "").strip()
        phone_number_id = str((value.get("metadata") or {}).get("phone_number_id") or "").strip()
        
        logger.info(f"From: {from_number}, Phone ID: {phone_number_id}")
        
        # Extract message text
        text = ""
        interactive = message_obj.get("interactive") or {}
        if isinstance(interactive, dict) and "button_reply" in interactive:
            text = str((interactive.get("button_reply") or {}).get("id") or "")
        elif isinstance(interactive, dict) and "list_reply" in interactive:
            text = str((interactive.get("list_reply") or {}).get("id") or "")
        else:
            text = str((message_obj.get("text") or {}).get("body") or "")
        
        logger.info(f"Message text: {text}")
        
        # Check if WhatsApp credentials are available
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        if not access_token:
            logger.error("WHATSAPP_ACCESS_TOKEN not found in environment")
            logger.error("Available environment variables:")
            for key in ["WHATSAPP_ACCESS_TOKEN", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_API_VERSION", "FACEBOOK_APP_SECRET"]:
                value = os.getenv(key)
                logger.error(f"  {key}: {'SET' if value else 'NOT SET'}")
            return JSONResponse({"ok": False, "error": "WhatsApp access token missing"}, status_code=500)
        
        logger.info("✅ WhatsApp credentials found, processing message...")
        
        # Process message
        session_id = from_number or None
        sid, reply = _ENGINE.handle_message(session_id=session_id, text=text, is_whatsapp=True)
        
        logger.info(f"Engine response: {reply}")
        
        # Handle special WhatsApp responses
        if reply == "LANGUAGE_SELECTION":
            message = "Afyabot (Afya+)\nHabari! Karibu Afya+. Chaguo bora kwa afya yako.\n\nChagua lugha:"
            buttons = [
                {"id": "1", "title": "Kiswahili"},
                {"id": "2", "title": "English"}
            ]
            logger.info("📤 Sending language selection buttons...")
            result = send_whatsapp_buttons(phone_number_id=phone_number_id, to=from_number, message=message, buttons=buttons)
            logger.info(f"Buttons sent: {result}")
        elif reply == "MAIN_MENU":
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
            logger.info("📤 Sending main menu list...")
            result = send_whatsapp_list(phone_number_id=phone_number_id, to=from_number, message=message, sections=sections)
            logger.info(f"List sent: {result}")
        elif phone_number_id and from_number:
            logger.info(f"📤 Sending text message: {reply}")
            result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=reply)
            logger.info(f"Text sent: {result}")
        
        logger.info("✅ Webhook processing completed successfully")
        return JSONResponse({"ok": True, "session_id": sid})
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ WhatsApp webhook error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
