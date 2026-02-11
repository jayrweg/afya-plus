// Simple WhatsApp webhook for testing
require('dotenv').config();

const WHATSAPP_ACCESS_TOKEN = process.env.WHATSAPP_ACCESS_TOKEN;
const WHATSAPP_VERIFY_TOKEN = process.env.WHATSAPP_VERIFY_TOKEN;
const WHATSAPP_PHONE_NUMBER_ID = process.env.WHATSAPP_PHONE_NUMBER_ID;

export default async function handler(req, res) {
    try {
        // Webhook verification
        if (req.method === 'GET') {
            const mode = req.query['hub.mode'];
            const token = req.query['hub.verify_token'];
            const challenge = req.query['hub.challenge'];
            
            if (mode === 'subscribe' && token === WHATSAPP_VERIFY_TOKEN) {
                res.status(200).send(challenge);
                return;
            } else {
                res.status(403).send('Verification failed');
                return;
            }
        }
        
        // Handle messages
        if (req.method === 'POST') {
            const data = req.body;
            
            if (!data.entry || !data.entry[0] || !data.entry[0].changes) {
                res.status(200).json({ ok: true, status: 'no_messages' });
                return;
            }
            
            const value = data.entry[0].changes[0].value;
            const messages = value.messages || [];
            
            if (messages.length === 0) {
                res.status(200).json({ ok: true, status: 'no_messages' });
                return;
            }
            
            const message = messages[0];
            const from = message.from;
            const phone_number_id = value.metadata?.phone_number_id;
            
            // Extract message text
            let text = '';
            if (message.text) {
                text = message.text.body.toLowerCase();
            } else if (message.interactive?.button_reply) {
                text = message.interactive.button_reply.id;
            } else if (message.interactive?.list_reply) {
                text = message.interactive.list_reply.id;
            }
            
            console.log('Received message:', text);
            
            // Simple bot logic
            let response;
            if (text === 'hi' || text === 'hello' || text === 'habari') {
                response = 'Hello! Welcome to Afyabot. Say "menu" to see options.';
            } else if (text === 'menu') {
                response = 'Choose an option:\n1. Doctor\n2. Pharmacy\n3. Emergency';
            } else if (text === '1') {
                response = 'Doctor selected. Please describe your symptoms.';
            } else if (text === '2') {
                response = 'Pharmacy selected. What medicine do you need?';
            } else if (text === '3') {
                response = 'Emergency! Call 911 immediately.';
            } else {
                response = 'Say "hi" to start or "menu" for options.';
            }
            
            // Send response
            const url = `https://graph.facebook.com/v19.0/${WHATSAPP_PHONE_NUMBER_ID}/messages`;
            const payload = {
                messaging_product: 'whatsapp',
                to: from,
                type: 'text',
                text: { body: response }
            };
            
            const whatsappResponse = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${WHATSAPP_ACCESS_TOKEN}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            console.log('WhatsApp response:', await whatsappResponse.json());
            
            res.status(200).json({ ok: true, message: 'Response sent' });
            return;
        }
        
        res.status(405).json({ error: 'Method not allowed' });
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: error.message });
    }
}
