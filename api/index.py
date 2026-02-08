import json
import logging
import os
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing WhatsApp functions
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whatsapp_cloud import send_whatsapp_text, send_whatsapp_buttons, send_whatsapp_list
from afyabot_types import Language

# Simple engine import
from engine import AfyabotEngine

# Initialize engine
_ENGINE = AfyabotEngine()

# WhatsApp credentials
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Afyabot WhatsApp API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/whatsapp/webhook")
def whatsapp_webhook_get(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    logger.info(f"Webhook verification request: mode={mode}, token={token}")
    
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return Response(content=challenge, status_code=200)
    else:
        logger.warning(f"❌ Webhook verification failed: mode={mode}, token={token}")
        raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook_post(request: Request):
    try:
        data = await request.json()
        logger.info("=== WHATSAPP WEBHOOK POST REQUEST ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Raw body: {json.dumps(data)}")
        logger.info("WhatsApp webhook POST received")
        logger.info(f"Webhook data: {data}")
        
        # Extract message data
        if not data.get("entry"):
            logger.info("No entry in webhook data")
            return JSONResponse({"ok": True, "status": "no_entry"})
        
        entry = data["entry"][0]
        changes = entry.get("changes", [])
        if not changes:
            logger.info("No changes in entry")
            return JSONResponse({"ok": True, "status": "no_changes"})
        
        change = changes[0]
        value = change.get("value", {})
        
        # Check if this is a message
        messages = value.get("messages", [])
        logger.info(f"Messages found: {len(messages)}")
        
        if not messages:
            logger.info("No messages in webhook - this might be a status update")
            return JSONResponse({"ok": True, "status": "no_messages"})
        
        message_obj = messages[0]
        from_number = str(message_obj.get("from", "")).strip()
        phone_number_id = str(value.get("metadata", {}).get("phone_number_id", "")).strip()
        
        logger.info(f"From: {from_number}, Phone ID: {phone_number_id}")
        
        # Extract message text
        text = ""
        if "text" in message_obj:
            text = str(message_obj["text"].get("body", ""))
        elif "interactive" in message_obj:
            interactive = message_obj["interactive"]
            if "button_reply" in interactive:
                text = str(interactive["button_reply"].get("id", ""))
            elif "list_reply" in interactive:
                text = str(interactive["list_reply"].get("id", ""))
        
        logger.info(f"Message text: {text}")
        
        # Process message
        session_id = from_number or None
        response = _ENGINE.handle_message(session_id=session_id, text=text, is_whatsapp=True)
        
        # Handle both tuple and direct string responses
        if isinstance(response, tuple) and len(response) == 2:
            sid, reply = response
        else:
            sid, reply = response, response  # Fallback for unexpected format
        
        # Handle WhatsApp responses using existing functions
        if reply == "LANGUAGE_SELECTION":
            # Check if user has chosen language before
            session = _ENGINE.sessions.get(from_number)
            if session and session.language == Language.EN:
                message = """Afya+
Hello!
Welcome to Afyaplus - Better health solutions
We bring healthcare closer to you
Choose language:"""
                buttons = [
                    {"id": "1", "title": "Swahili"},
                    {"id": "2", "title": "English"}
                ]
            else:
                message = """Afya+
Habari!
Karibu afyaplus chaguo bora kwa afya yako
Tunakusogeza karibu na matibabu kupata suluhisho bora kwa afya yako
Chagua lugha"""
                buttons = [
                    {"id": "1", "title": "Kiswahili"},
                    {"id": "2", "title": "English"}
                ]
            logger.info("📤 Sending language selection buttons...")
            result = send_whatsapp_buttons(phone_number_id=phone_number_id, to=from_number, message=message, buttons=buttons)
            logger.info(f"Buttons sent: {result}")
            
        elif reply == "MAIN_MENU":
            # Check language and show appropriate menu
            session = _ENGINE.sessions.get(from_number)
            if session and session.language == Language.EN:
                message = """Afyaplus offers the following services:"""
                sections = [{
                    "title": "Medical Services",
                    "rows": [
                        {"id": "1", "title": "🩺 General Practitioner"},
                        {"id": "2", "title": "👨‍⚕️ Specialist Doctor"},
                        {"id": "3", "title": "🏠 Home Doctor"},
                        {"id": "4", "title": "🏢 Workplace Health"},
                        {"id": "5", "title": "💊 Pharmacy"}
                    ]
                }]
                button_text = "Choose service"
            else:
                message = """Afyaplus inakuletea huduma zifuatazo,chagua"""
                sections = [{
                    "title": "Matibabu",
                    "rows": [
                        {"id": "1", "title": "🩺 Daktari jumla (GP)"},
                        {"id": "2", "title": "👨‍⚕️ Daktari bingwa"},
                        {"id": "3", "title": "🏠 Daktari nyumbani"},
                        {"id": "4", "title": "🏢 Afya ya kazi"},
                        {"id": "5", "title": "💊 Dawa na madawa"}
                    ]
                }]
                button_text = "Chagua huduma"
            logger.info("📤 Sending main menu list...")
            result = send_whatsapp_list(phone_number_id=phone_number_id, to=from_number, message=message, sections=sections, button_text=button_text)
            logger.info(f"List sent: {result}")
            
        elif reply == "COLLECT_NAME":
            message = "Andika jina lako kamili:"
            logger.info("📤 Sending name collection request...")
            result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Name request sent: {result}")
            
        elif reply == "COLLECT_PHONE":
            message = "Asante! Sasa andika namba yako ya simu (inaanza na 255, 0, au +255):"
            logger.info("📤 Sending phone collection request...")
            result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Phone request sent: {result}")
            
        elif reply == "COLLECT_NAME_ERROR":
            message = "Jina lako ni fupi sana. Tafadhali andika jina kamili."
            logger.info("📤 Sending name error message...")
            result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Name error sent: {result}")
            
        elif reply == "COLLECT_PHONE_ERROR":
            message = "Namba ya simu si sahihi. Tumia namba inaanza na 255, 0, au +255"
            logger.info("📤 Sending phone error message...")
            result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Phone error sent: {result}")
            
        elif reply == "PAYMENT_SUMMARY":
            # Create payment summary with character limits
            session = _ENGINE.sessions.get(from_number)
            order = session.active_order if session and hasattr(session, 'active_order') and session.active_order else None
            if order:
                message = f"""📋 Muhtasari wa Malipo
Huduma: {order.service_name}
Bei: TZS {order.amount_tzs:,}
Jina: {order.user_name}
Simu: {order.user_phone}

Namba ya malipo: {order.token}

Tuma pesa kwa namba:
- M-Pesa: 123456789
- Tigo Pesa: 987654321
- Airtel Money: 456789123

Baada ya malipo, tuma 'paid {order.token}'"""
            else:
                message = "Kuna tatizo na muhtasari wako. Tafadhali anza tena."
            logger.info("📤 Sending payment summary...")
            result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Payment summary sent: {result}")
            
        elif reply == "GP_MENU":
            session = _ENGINE.sessions.get(from_number)
            if session and session.language == Language.EN:
                message = """🩺 General Practitioner Services

Treat common illnesses:
• Acne, Eczema, Allergies
• Asthma, Pressure, Diabetes  
• Flu, Fever, Cough
• Back pain, Headaches
• UTI, Diarrhea, Dizziness

Choose connection method:"""
                buttons = [
                    {"id": "1", "title": "Chat - TZS 3,000"},
                    {"id": "2", "title": "Video - TZS 5,000"}
                ]
                logger.info("📤 Sending GP menu buttons (EN)...")
                result = send_whatsapp_buttons(phone_number_id=phone_number_id, to=from_number, message=message, buttons=buttons)
            else:
                message = """🩺 Huduma ya Daktari Jumla (GP)

Tibu magonjwa ya kawaida:
• Chunusi, Eczema, Mzio
• Pumu, Presha, Sukari
• Mafua, Homna, Kikohozi
• Maumivu ya mgongo, kichwa
• UTI, Kuhara, Kizunguzungu

Chagua njia:"""
                buttons = [
                    {"id": "1", "title": "Chat - TZS 3,000"},
                    {"id": "2", "title": "Video - TZS 5,000"}
                ]
                logger.info("📤 Sending GP menu buttons (SW)...")
                result = send_whatsapp_buttons(phone_number_id=phone_number_id, to=from_number, message=message, buttons=buttons)
            logger.info(f"GP menu sent: {result}")
            
        elif reply == "SPECIALIST_MENU":
            session = _ENGINE.sessions.get(from_number)
            if session and session.language == Language.EN:
                message = """👨‍⚕️ Specialist Doctor Services

For long-term conditions:
• Skin diseases
• Women's health & fertility
• Children, Heart, Pressure
• Bones, Blood vessels
• Digestion, Allergies

Choose connection method:"""
                buttons = [
                    {"id": "1", "title": "Chat - TZS 25,000"},
                    {"id": "2", "title": "Video - TZS 30,000"}
                ]
                logger.info("📤 Sending Specialist menu buttons (EN)...")
                result = send_whatsapp_buttons(phone_number_id=phone_number_id, to=from_number, message=message, buttons=buttons)
            else:
                message = """👨‍⚕️ Huduma ya Daktari Bingwa

Kwa magonjwa ya muda mrefu:
• Magonjwa ya ngozi
• Uzazi na wanawake
• Watoto, Moyo, Presha
• Mifupa, Mishipa
• Chakula, Allergy

Chagua njia:"""
                buttons = [
                    {"id": "1", "title": "Chat - TZS 25,000"},
                    {"id": "2", "title": "Video - TZS 30,000"}
                ]
                logger.info("📤 Sending Specialist menu buttons (SW)...")
                result = send_whatsapp_buttons(phone_number_id=phone_number_id, to=from_number, message=message, buttons=buttons)
            logger.info(f"Specialist menu sent: {result}")
            
        elif reply == "HOME_DOCTOR_MENU":
            session = _ENGINE.sessions.get(from_number)
            if session and session.language == Language.EN:
                message = """🏠 Home Doctor Services

We come to your home:
1. Quick treatment - TZS 30,000
2. Medical procedure - TZS 30,000  
3. AMD guidance - TZS 50,000
4. SDA assessment - TZS 30,000

Choose service (1-4)"""
                logger.info("📤 Sending Home Doctor menu (EN)...")
                result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            else:
                message = """🏠 Daktari Nyumbani

Tunakuja kwako nyumbani:
1. Matibabu ya haraka - TZS 30,000
2. Matibabu procedure - TZS 30,000  
3. Mwongozo AMD - TZS 50,000
4. Tathmini SDA - TZS 30,000

Chagua huduma (1-4)"""
                logger.info("📤 Sending Home Doctor menu (SW)...")
                result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Home Doctor menu sent: {result}")
            
        elif reply == "WORKPLACE_MENU":
            session = _ENGINE.sessions.get(from_number)
            if session and session.language == Language.EN:
                message = """🏢 Workplace Health Services

For employees:
1. Pre-employment tests - TZS 10,000
2. Vaccination & screening - TZS 10,000
3. Health wellness talks - TZS 10,000

Choose service (1-3)"""
                logger.info("📤 Sending Workplace menu (EN)...")
                result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            else:
                message = """🏢 Afya ya Kazi

Kwa wafanyakazi:
1. Vipimo kabla ya kazi - TZS 10,000
2. Chanjo na uchunguzi - TZS 10,000
3. Mada za afya - TZS 10,000

Chagua huduma (1-3)"""
                logger.info("📤 Sending Workplace menu (SW)...")
                result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Workplace menu sent: {result}")
            
        elif reply == "PHARMACY_MENU":
            session = _ENGINE.sessions.get(from_number)
            if session and session.language == Language.EN:
                message = """💊 Pharmacy Services

Get medicines & supplies:
• Doctor prescriptions
• Medical equipment  
• Vitamins & supplements
• Medicine advice

Price: TZS 4,000

Send '1' to continue"""
                logger.info("📤 Sending Pharmacy menu (EN)...")
                result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            else:
                message = """💊 Duka la Dawa

Pata dawa na vifaa:
• Dawa za daktari
• Vifaa vya matibabu  
• Vitamins na supplements
• Ushauri wa dawa

Bei: TZS 4,000

Tuma '1' kuendelea"""
                logger.info("📤 Sending Pharmacy menu (SW)...")
                result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=message)
            logger.info(f"Pharmacy menu sent: {result}")
            
        else:
            # Send as text message for now
            logger.info("📤 Sending text message...")
            result = send_whatsapp_text(phone_number_id=phone_number_id, to=from_number, message=reply)
            logger.info(f"Text message sent: {result}")
        
        logger.info("✅ Webhook processing completed successfully")
        return JSONResponse({"ok": True, "status": "success"})
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
