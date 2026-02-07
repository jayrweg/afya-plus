import json
import logging
import os
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        sid, reply = _ENGINE.handle_message(session_id=session_id, text=text, is_whatsapp=True)
        
        logger.info(f"Engine response: {reply}")
        
        # Handle WhatsApp responses
        if reply == "LANGUAGE_SELECTION":
            await send_language_selection(phone_number_id, from_number)
        elif reply == "MAIN_MENU":
            await send_main_menu(phone_number_id, from_number)
        elif reply == "GP_MENU":
            await send_gp_menu(phone_number_id, from_number)
        elif reply == "SPECIALIST_MENU":
            await send_specialist_menu(phone_number_id, from_number)
        elif reply == "HOME_DOCTOR_MENU":
            await send_home_doctor_menu(phone_number_id, from_number)
        elif reply == "WORKPLACE_MENU":
            await send_workplace_menu(phone_number_id, from_number)
        elif reply == "PHARMACY_MENU":
            await send_pharmacy_menu(phone_number_id, from_number)
        else:
            # Send as text message for now
            await send_text_message(phone_number_id, from_number, reply)
        
        logger.info("✅ Webhook processing completed successfully")
        return JSONResponse({"ok": True, "status": "success"})
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

async def send_language_selection(phone_number_id: str, to: str):
    """Send language selection buttons"""
    import httpx
    
    message = """Afya+
Habari!
Karibu afyaplus chaguo bora kwa afya yako
Tunakusogeza karibu na matibabu kupata suluhisho bora kwa afya yako
Chagua lugha"""
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": message},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "1", "title": "Kiswahili"}},
                    {"type": "reply", "reply": {"id": "2", "title": "English"}}
                ]
            }
        }
    }
    
    url = f"https://graph.facebook.com/v24.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        logger.info(f"📤 Language selection sent: {response.status_code}")
        logger.info(f"Response: {response.text}")

async def send_main_menu(phone_number_id: str, to: str):
    """Send main menu list"""
    import httpx
    
    message = """Afyaplus inakuletea huduma zifuatazo,chagua"""
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": message},
            "action": {
                "button": "Chagua huduma",
                "sections": [
                    {
                        "title": "Matibabu",
                        "rows": [
                            {"id": "1", "title": "🩺 Kuwasiliana na daktari jumla(GP)"},
                            {"id": "2", "title": "👨‍⚕️ Kuwasiliana na daktari bingwa(specialist)"},
                            {"id": "3", "title": "🏠 Huduma ya daktari nyumbani(homedoctor)"},
                            {"id": "4", "title": "🏢 Afya mazingira ya kazi(corporate)"},
                            {"id": "5", "title": "💊 Ushauri ,maelekezo ya dawa(pharmacy)"}
                        ]
                    }
                ]
            }
        }
    }
    
    url = f"https://graph.facebook.com/v24.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        logger.info(f"📤 Main menu sent: {response.status_code}")
        logger.info(f"Response: {response.text}")

async def send_gp_menu(phone_number_id: str, to: str):
    """Send GP service info"""
    message = """Afya+ inakuunganisha na daktari kwa ushauri na matibabu papo hapo kiganjani mwako.

Tibu magonjwa ya kawaida na yale ya muda mrefu bila usumbufu wa kusafiri:
• Chunusi, Mapunye, na Eczema
• Mzio (Allergies)
• Wasiwasi na Msongo wa Mawazo
• Pumu (Asthma)
• Maumivu ya Mgongo
• Uzazi wa Mpango
• Mafua, Homa, na Kikohozi
• Ugonjwa wa Kisukari
• Kuhara
• Kizunguzungu
• Maambukizi ya Masikio
• Upungufu wa Nguvu za Kiume
• Ugonjwa wa magoti
• Kukatika kwa Nywele
• Shinikizo la Juu la Damu
• Kichwa Migraine
• Macho Mekundu
• Matatizo ya Sinus/Pua
• Maumivu ya Koo
• Maambukizi ya Njia ya Mkojo - UTI
• Kutapika
• Kupunguza Uzito

Chagua njia ya kuunganishwa:
1. Kuunganishwa kwa kuchati kwenye simu 3k tzs
2. Kuunganishwa kwa whatsapp video call 5ktzs"""
    
    await send_text_message(phone_number_id, to, message)

async def send_specialist_menu(phone_number_id: str, to: str):
    """Send Specialist service info"""
    message = """Ikiwa unakabiliana na dalili endelevu, na magonjwa ya muda mrefu, au unahitaji ushauri wa kitaalamu kwa tatizo maalum la kiafya, huenda wakati umefika wa kuzungumza na daktari bingwa.

Afya+ inakusaidia kupata Ushauri wa kidijitali ni msaada mkubwa hasa katika kupitia majibu ya vipimo, kujadili chaguzi za matibabu, au kupata maoni ya pili ya kitaalamu bila kuhitaji kusafiri au kusubiri kliniki.

Iwe ni:
● Magonjwa ya ngozi
● Magonjwa ya uzazi na wanawake
● Watoto
● Moyo, presha na sukari, magonjwa ya ndani kwa ujumla
● Mifupa
● Mfumo wa mmeng'enyo wa chakula au fani nyinginezo

Chagua njia ya kuunganishwa:
1. Kuwasiliana na daktari bingwa kwa kuchati (25k)
2. Kuwasiliana na daktari bingwa kwa video call(30k)"""
    
    await send_text_message(phone_number_id, to, message)

async def send_home_doctor_menu(phone_number_id: str, to: str):
    """Send Home Doctor service info"""
    message = """Afya+ inakuletea Daktari wa nyumbani kuleta huduma bora za afya moja kwa moja hadi mlangoni pako. Kama vile kupata klinika ya daktari wa kawaida (GP), madaktari wetu wenye leseni wanatoa ushauri wa kitaalamu — lakini kwa ana kwa ana, katika starehe na faragha ya nyumba yako. Epuka foleni za kliniki — sisi tunakuja kwako.

Chagua huduma:
1. Matibabu ya haraka - Pata huduma za matibabu ya ana kwa ana kwa magonjwa ya kawaida kama mafua, maambukizi madogo, na dalili nyinginezo ambazo si za dharura — zote kwa pamoja. (30k)
2. Taratibu Tiba/medical procedure - Pata huduma salama za kitabibu zinazotolewa na wataalamu katika utulivu wa nyumbani kwako — ikijumuisha usimamizi wa dawa, huduma za dripu (IV), kusafisha vidonda vya upasuaji, huduma ya kwanza, na uchukuaji wa sampuli za vipimo. (30k)
3. Mwongozo wa matibabu(advanced medical directives) - AMD ni waraka wa kisheria unaokuwezesha kuandika mapema maamuzi yako ya matibabu endapo utashindwa kuwasiliana siku zijazo. Madaktari wetu hutoa ushauri wa kitabibu nyumbani kukueleza AMD, kukusaidia kufanya maamuzi sahihi, na kuthibitisha maombi yako ya AMD. (50k)
4. Tathmini ya Ulemavu (SDA) - Madaktari wetu hufanya tathmini ya kitaalamu nyumbani kwako ili kuangalia uwezo wa kumudu shughuli za kila siku, kama vile kuoga, kuvaa, kula, na uwezo wa kutembea. (30k)

Chagua namba ya huduma (1-4)"""
    
    await send_text_message(phone_number_id, to, message)

async def send_workplace_menu(phone_number_id: str, to: str):
    """Send Workplace service info"""
    message = """Huduma za afya kwa mashirika kutoka Afyaplus zimeundwa kwa ajili ya biashara za ukubwa wowote, uwe ni kampuni kubwa, biashara ndogo na za kati (SME), au kampuni changa yenye wafanyakazi nchini Tanzania.

Chagua huduma:
1. Kwa Vipimo vya afya kabla ya kuanza ajira - Uchunguzi wa afya mapema huwezesha usaidizi wa kitabibu kwa wakati, jambo ambalo hupunguza hatari ya matatizo ya muda mrefu na kuimarisha hali ya afya kwa kabla ya kuanza kazi. (10k)
2. Uchunguzi wa afya (Screening) na chanjo - Huduma za chanjo husaidia kupunguza kuenea kwa magonjwa mahali pa kazi, kupunguza utoro kazini, na kuwalinda wafanyakazi walio katika hatari zaidi. (10k)
3. Mada na semina za afya(workplace wellness solutions) - Jenga timu yenye afya, furaha, na tija zaidi kupitia mihadhara, warsha, na wavuti za ustawi zinazoendeshwa na wataalamu na kulingana na mahitaji ya taasisi yako.

Mada zetu kuu ni pamoja na:
• Afya ya akili na udhibiti wa msongo wa mawazo
• Umakinifu (Mindfulness) kwa ajili ya kuongeza umakini na tija
• Usingizi bora na kuongeza nguvu ya mwili
• Fikra chanya na ustahimilivu
• Hamasisho na ufikiaji wa malengo

Chagua namba ya huduma (1-3)"""
    
    await send_text_message(phone_number_id, to, message)

async def send_pharmacy_menu(phone_number_id: str, to: str):
    """Send Pharmacy service info"""
    message = """Nunua bidhaa za afya na ustawi kwa ushauri wa kitaalamu kutoka kwa madaktari, pamoja na maelekezo sahihi ya matumizi ya dawa (prescriptions) kulingana na mahitaji yako.

Tunahakikisha huduma salama, rahisi, na ya kuaminika, ili kukusaidia kulinda na kuboresha afya yako kwa uhakika.

Bonyeza link ifuatayo kupata huduma hii:
Shop health and wellness 4k"""
    
    await send_text_message(phone_number_id, to, message)

async def send_text_message(phone_number_id: str, to: str, message: str):
    """Send a simple text message"""
    import httpx
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    
    url = f"https://graph.facebook.com/v24.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        logger.info(f"📤 Text message sent: {response.status_code}")
        logger.info(f"Response: {response.text}")
