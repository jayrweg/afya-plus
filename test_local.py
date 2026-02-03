#!/usr/bin/env python3
"""
Local test server for Vercel serverless functions
Simulates Vercel's API environment locally
"""

import json
import sys
import os
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Add afyabot to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our serverless functions
from api.chat import handler as chat_handler
from api.whatsapp import handler as whatsapp_handler

class LocalTestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        """Send JSON response"""
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def _send_text(self, status, text):
        """Send plain text response"""
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/health':
            self._send_json(200, {"status": "ok", "service": "afyabot-local"})
        
        elif path == '/api/whatsapp/webhook':
            # Simulate Vercel request object
            class MockRequest:
                def __init__(self, method, args):
                    self.method = method
                    self.args = args
            
            query = parse_qs(parsed.query)
            print(f"[DEBUG] Raw query: {query}")
            # Convert lists to strings for single values
            for key in query:
                if isinstance(query[key], list) and len(query[key]) == 1:
                    query[key] = query[key][0]
            print(f"[DEBUG] Processed query: {query}")
            
            mock_request = MockRequest('GET', query)
            
            try:
                result = whatsapp_handler(mock_request)
                if result.get('statusCode') == 200:
                    self._send_text(result['statusCode'], result.get('body', ''))
                else:
                    self._send_json(result['statusCode'], {"error": result.get('body', 'Error')})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        
        elif path == '/' or path == '/index.html':
            # Serve the test UI
            try:
                with open('public/index.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self._send_json(404, {"error": "Test UI not found"})
        
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Read request body
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        try:
            json_data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except json.JSONDecodeError:
            json_data = {}
        
        # Simulate Vercel request object
        class MockRequest:
            def __init__(self, method, json_data):
                self.method = method
                self._json = json_data
            
            def get_json(self):
                return self._json
        
        mock_request = MockRequest('POST', json_data)
        
        if path == '/api/chat':
            try:
                result = chat_handler(mock_request)
                self._send_json(result['statusCode'], json.loads(result.get('body', '{}')))
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        
        elif path == '/api/whatsapp/webhook':
            try:
                result = whatsapp_handler(mock_request)
                self._send_json(result['statusCode'], json.loads(result.get('body', '{}')))
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        
        else:
            self._send_json(404, {"error": "Not found"})

def main():
    """Run the local test server"""
    port = 8008
    server_address = ('', port)
    
    print(f"🚀 Afyabot Local Test Server")
    print(f"📍 Server running on http://localhost:{port}")
    print(f"🌐 Test UI: http://localhost:{port}/")
    print(f"💬 Chat API: http://localhost:{port}/api/chat")
    print(f"📱 WhatsApp Webhook: http://localhost:{port}/api/whatsapp/webhook")
    print(f"❤️  Health: http://localhost:{port}/health")
    print()
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd = HTTPServer(server_address, LocalTestHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    main()
