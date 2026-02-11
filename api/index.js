// Simple WhatsApp webhook for testing

const WHATSAPP_ACCESS_TOKEN = process.env.WHATSAPP_ACCESS_TOKEN;
const WHATSAPP_VERIFY_TOKEN = process.env.WHATSAPP_VERIFY_TOKEN;
const WHATSAPP_PHONE_NUMBER_ID = process.env.WHATSAPP_PHONE_NUMBER_ID;

module.exports = async function handler(req, res) {
    try {
        // Check if environment variables are set
        if (!WHATSAPP_ACCESS_TOKEN || !WHATSAPP_VERIFY_TOKEN || !WHATSAPP_PHONE_NUMBER_ID) {
            console.error('Missing environment variables');
            res.status(500).json({ error: 'Server configuration error' });
            return;
        }
        
        // Webhook verification
        if (req.method === 'GET') {
            const mode = req.query['hub.mode'];
            const token = req.query['hub.verify_token'];
            const challenge = req.query['hub.challenge'];
            
            console.log('Webhook verification attempt:');
            console.log('Mode:', mode);
            console.log('Token:', token);
            console.log('Expected Token:', WHATSAPP_VERIFY_TOKEN);
            console.log('Challenge:', challenge);
            
            if (mode === 'subscribe' && token === WHATSAPP_VERIFY_TOKEN) {
                console.log('✅ Verification successful');
                res.status(200).send(challenge);
                return;
            } else {
                console.log('❌ Verification failed');
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
            
            // Handle interactive responses
            if (text === 'swahili') {
                response = 'Karibu Afyaplus! Nini unahitaji kusaidia?';
            } else if (text === 'english') {
                response = 'Welcome to Afyaplus! How can we help you today?';
            } else if (text === 'doctor') {
                response = 'Doctor consultation selected. Please describe your symptoms and we will connect you with a doctor.';
            } else if (text === 'pharmacy') {
                response = 'Pharmacy selected. Please tell us what medicine you need or describe your condition.';
            } else if (text === 'emergency') {
                response = 'Emergency services activated! Please share your location and we will send immediate assistance.';
            } else {
                response = 'Say "hi" to start or "menu" for options.';
            }
            
            // Send response
            const url = `https://graph.facebook.com/v19.0/${WHATSAPP_PHONE_NUMBER_ID}/messages`;
            
            let payload;
            
            if (text === 'hi' || text === 'hello' || text === 'habari') {
                // Send interactive buttons for language selection
                payload = {
                    messaging_product: 'whatsapp',
                    to: from,
                    type: 'interactive',
                    interactive: {
                        type: 'button',
                        body: {
                            text: 'Welcome to Afyaplus! Please select your preferred language:'
                        },
                        action: {
                            buttons: [
                                {
                                    type: 'reply',
                                    reply: {
                                        id: 'swahili',
                                        title: 'Kiswahili'
                                    }
                                },
                                {
                                    type: 'reply',
                                    reply: {
                                        id: 'english',
                                        title: 'English'
                                    }
                                }
                            ]
                        }
                    }
                };
            } else if (text === 'menu') {
                // Send interactive list menu
                payload = {
                    messaging_product: 'whatsapp',
                    to: from,
                    type: 'interactive',
                    interactive: {
                        type: 'list',
                        header: {
                            type: 'text',
                            text: 'Afyaplus Services'
                        },
                        body: {
                            text: 'Please select a service from menu:'
                        },
                        footer: {
                            text: 'Better health solutions'
                        },
                        action: {
                            button: 'Choose service',
                            sections: [
                                {
                                    title: 'Medical Services',
                                    rows: [
                                        {
                                            id: 'doctor',
                                            title: 'Doctor Consultation',
                                            description: 'Talk to a doctor now'
                                        },
                                        {
                                            id: 'pharmacy',
                                            title: 'Pharmacy',
                                            description: 'Order medicines and supplies'
                                        },
                                        {
                                            id: 'emergency',
                                            title: 'Emergency',
                                            description: 'Urgent medical assistance'
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                };
            } else {
                // Send text response for other messages
                payload = {
                    messaging_product: 'whatsapp',
                    to: from,
                    type: 'text',
                    text: { body: response }
                };
            }
            
            try {
                const whatsappResponse = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${WHATSAPP_ACCESS_TOKEN}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await whatsappResponse.json();
                console.log('WhatsApp response:', result);
            } catch (fetchError) {
                console.error('Fetch error:', fetchError);
            }
            
            res.status(200).json({ ok: true, message: 'Response sent' });
            return;
        }
        
        res.status(405).json({ error: 'Method not allowed' });
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: error.message });
    }
}
