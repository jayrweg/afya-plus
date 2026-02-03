from __future__ import annotations

from typing import Dict

from types import Language


_TEXT: Dict[Language, Dict[str, str]] = {
    Language.SW: {
        "greeting": "Habari! Karibu Afya+. Chaguo bora kwa afya yako.",
        "choose_language": "Chagua lugha:\n1) Kiswahili\n2) English",
        "invalid_language": "Tafadhali chagua lugha sahihi: 1 kwa Kiswahili au 2 kwa English.",
        "main_menu": (
            "Afyaplus inakuletea huduma zifuatazo, chagua:\n"
            "1) Kuwasiliana na daktari jumla (GP)\n"
            "2) Kuwasiliana na daktari bingwa (Specialist)\n"
            "3) Huduma ya daktari nyumbani (Home Doctor)\n"
            "4) Afya mazingira ya kazi (Corporate)\n"
            "5) Ushauri/maelekezo ya dawa na vifaa tiba (Pharmacy)\n\n"
            "Andika namba (1-5) au neno (mfano: gp)."
        ),
        "fallback": "Sijaelewa. Andika 'menu' kurudi kwenye menyu au 'start' kuanza upya.",
        "disclaimer": (
            "Kumbuka: Afyabot hatoi utambuzi rasmi wa ugonjwa. Kwa dharura piga simu huduma ya dharura ya eneo lako mara moja."
        ),
        "gp_info": (
            "Afya+ inakuunganisha na daktari kwa ushauri na matibabu papo hapo.\n"
            "Husaidia magonjwa ya kawaida na sugu kama: chunusi/eczema, mzio, wasiwasi, pumu, maumivu ya mgongo, uzazi wa mpango, mafua/homa/kikohozi, kisukari, UTI n.k."
        ),
        "gp_channel": "Chagua njia ya huduma:\n1) Kuchati kwenye simu (TZS 100)\n2) WhatsApp video call (TZS 200)",
        "specialist_info": (
            "Afya+ inakuunganisha na daktari bingwa kwa ushauri wa kitaalamu (ngozi, uzazi/wanawake, watoto, moyo/presha/sukari, mifupa, mmeng'enyo n.k.)."
        ),
        "specialist_channel": "Chagua njia:\n1) Kuchati (TZS 300)\n2) Video call (TZS 300)",
        "home_doctor_menu": (
            "Huduma ya daktari nyumbani. Chagua:\n"
            "1) Matibabu ya haraka (TZS 300)\n"
            "2) Taratibu tiba / Medical procedure (TZS 300)\n"
            "3) Mwongozo wa matibabu (AMD) (TZS 300)\n"
            "4) Tathmini ya ulemavu (SDA) (TZS 300)"
        ),
        "workplace_menu": (
            "Afya mazingira ya kazi. Chagua:\n"
            "1) Pre-employment medical check (TZS 200)\n"
            "2) Health screening & vaccination (TZS 200)\n"
            "3) Workplace wellness solutions (TZS 200)"
        ),
        "pharmacy_menu": "Pharmacy: Shop health and wellness (TZS 100).",
        "checkout_created": "Ombi lako limeandaliwa. Fuata maelekezo ya malipo hapa chini:",
        "paid_ok": "Asante! Malipo yamepokelewa (demo). Tutafanya hatua ya kufuata.",
        "paid_invalid": "Siwezi kuthibitisha malipo. Tafadhali andika: paid <token>",
        "restart": "Sawa. Tuanze upya.",
        "ask_name": "Tafadhali andika jina lako kamili:",
        "ask_phone": "Tafadhali andika namba yako ya simu (mfano 0627404843):",
    },
    Language.EN: {
        "greeting": "Hello! Welcome to Afya+. The best choice for your health.",
        "choose_language": "Choose language:\n1) Kiswahili\n2) English",
        "invalid_language": "Please choose a valid language: 1 for Kiswahili or 2 for English.",
        "main_menu": (
            "Afya+ services (choose):\n"
            "1) Talk to a General Practitioner (GP)\n"
            "2) Talk to a Specialist\n"
            "3) Home Doctor services\n"
            "4) Corporate/Workplace health solutions\n"
            "5) Pharmacy guidance & wellness products\n\n"
            "Type a number (1-5) or a keyword (e.g. gp)."
        ),
        "fallback": "I didn't understand. Type 'menu' to go back or 'start' to restart.",
        "disclaimer": "Note: Afyabot is not a medical diagnosis. In emergencies, contact local emergency services immediately.",
        "gp_info": (
            "Afya+ connects you to a doctor for quick advice and treatment.\n"
            "Common conditions include: acne/rash/eczema, allergies, anxiety, asthma, back pain, birth control, cold/flu/fever/cough, diabetes, UTI and more."
        ),
        "gp_channel": "Choose a channel:\n1) Chat consultation (TZS 100)\n2) WhatsApp video call (TZS 200)",
        "specialist_info": (
            "Afya+ connects you to specialists for professional advice (dermatology, women's health, pediatrics, heart/BP/diabetes, orthopedics, digestive system and more)."
        ),
        "specialist_channel": "Choose a channel:\n1) Chat (TZS 300)\n2) Video call (TZS 300)",
        "home_doctor_menu": (
            "Home Doctor services. Choose:\n"
            "1) Quick treatment (TZS 300)\n"
            "2) Medical procedure (TZS 300)\n"
            "3) Advanced Medical Directives (AMD) (TZS 300)\n"
            "4) Severe Disability Assessment (SDA) (TZS 300)"
        ),
        "workplace_menu": (
            "Workplace health solutions. Choose:\n"
            "1) Pre-employment medical check (TZS 200)\n"
            "2) Health screening & vaccination (TZS 200)\n"
            "3) Workplace wellness solutions (TZS 200)"
        ),
        "pharmacy_menu": "Pharmacy: Shop health and wellness (TZS 100).",
        "checkout_created": "Your request is ready. Follow the payment instructions below:",
        "paid_ok": "Thank you! Payment received (demo). We'll proceed with the next step.",
        "paid_invalid": "I couldn't verify that payment. Please type: paid <token>",
        "restart": "Okay. Let's start again.",
        "ask_name": "Please enter your full name:",
        "ask_phone": "Please enter your phone number (e.g. 0627404843):",
    },
}


def t(lang: Language, key: str) -> str:
    return _TEXT.get(lang, _TEXT[Language.EN]).get(key, key)
