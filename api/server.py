import json
import os
from http.server import BaseHTTPRequestHandler
import sys

# Add afyabot to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing engine
from afyabot.engine import AfyabotEngine

_ENGINE = AfyabotEngine()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "afyabot-vercel"}).encode())
        elif self.path == '/':
            try:
                with open('public/index.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>Afyabot</h1><p>UI file not found</p>')
        elif self.path.startswith('/api/whatsapp/webhook'):
            # Handle webhook verification
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            
            mode = query.get('hub.mode', [''])[0]
            token = query.get('hub.verify_token', [''])[0]
            challenge = query.get('hub.challenge', [''])[0]
            verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
            
            if mode == 'subscribe' and token and verify_token and token == verify_token:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(challenge.encode())
            else:
                self.send_response(403)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Verification failed')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        if self.path == '/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                session_id = data.get("session_id")
                message = data.get("message", "")
                sid, reply = _ENGINE.handle_message(session_id=session_id, text=str(message))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "session_id": sid, "reply": reply}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
        
        elif self.path == '/api/whatsapp/webhook':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                entry = (data.get("entry") or [])[0] or {}
                changes = (entry.get("changes") or [])[0] or {}
                value = changes.get("value") or {}
                messages = value.get("messages") or []
                
                if not messages:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True, "status": "no_messages"}).encode())
                    return
                
                message_obj = messages[0] or {}
                from_number = str(message_obj.get("from") or "").strip()
                phone_number_id = str((value.get("metadata") or {}).get("phone_number_id") or "").strip()
                
                # Extract message text
                text = str((message_obj.get("text") or {}).get("body") or "")
                
                # Process message
                session_id = from_number or None
                sid, reply = _ENGINE.handle_message(session_id=session_id, text=text, is_whatsapp=True)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "session_id": sid}).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
