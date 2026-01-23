#!/usr/bin/env python3
"""
Prosty test API bez FastAPI - używa wbudowanego http.server
"""

import sys
from pathlib import Path
# Dodaj ścieżkę do src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen
import asyncio

# Import NLP2CMD
try:
    from nlp2cmd_web_controller import NLP2CMDWebAPI
    print("✓ NLP2CMDWebAPI imported successfully")
except ImportError as e:
    print(f"✗ Failed to import NLP2CMDWebAPI: {e}")
    sys.exit(1)

class NLP2CMDHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.api = NLP2CMDWebAPI(use_llm_fallback=True, auto_install=True)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>NLP2CMD Simple API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        input { width: 300px; padding: 10px; }
        button { padding: 10px 20px; }
        .result { margin-top: 20px; padding: 10px; background: #f0f0f0; }
    </style>
</head>
<body>
    <h1>NLP2CMD Simple API</h1>
    <form onsubmit="processCommand(event)">
        <input type="text" id="command" placeholder="Wpisz komendę (np. uruchom docker)" required>
        <button type="submit">Wykonaj</button>
    </form>
    <div id="result" class="result" style="display:none;"></div>
    
    <script>
        async function processCommand(e) {
            e.preventDefault();
            const cmd = document.getElementById('command').value;
            const result = document.getElementById('result');
            
            result.style.display = 'block';
            result.innerHTML = 'Przetwarzam...';
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd, dsl: 'auto' })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    result.innerHTML = `
                        <strong>Komenda:</strong> <code>${data.command || 'Brak'}</code><br>
                        <strong>DSL:</strong> ${data.dsl || 'unknown'}<br>
                        <strong>Wiadomość:</strong> ${data.message || ''}<br>
                        ${data.llm_used ? '<strong>✓ Użyto LLM fallback</strong>' : ''}
                    `;
                } else {
                    result.innerHTML = `<strong>Błąd:</strong> ${data.message}`;
                }
            } catch (error) {
                result.innerHTML = `<strong>Błąd:</strong> ${error.message}`;
            }
        }
    </script>
</body>
</html>
            """
            self.wfile.write(html.encode())
        elif self.path == '/status':
            self.send_json_response(self.api.get_status())
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/process':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('command', '')
                dsl = data.get('dsl', 'auto')
                
                # Uruchom async funkcję
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.api.process_command(command, dsl))
                finally:
                    loop.close()
                
                self.send_json_response(result)
            except Exception as e:
                self.send_json_response({
                    'status': 'error',
                    'message': str(e)
                })
        else:
            self.send_error(404)
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        # Cichy tryb - mniej logów
        pass

def run_server(port=8002):
    server_address = ('', port)
    httpd = HTTPServer(server_address, NLP2CMDHandler)
    print(f"🚀 NLP2CMD Simple API running on http://localhost:{port}")
    print("📝 Otwórz przeglądarkę i wpisz komendę np. 'uruchom docker'")
    print("🛑 Ctrl+C aby zatrzymać")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Zatrzymuję serwer...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
