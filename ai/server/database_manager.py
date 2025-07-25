from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional
import json, threading

LOCALHOST = 'localhost'
PORT = 8000

class DatabaseManager(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.database: Dict[str, Any] = {}
        self.lock = threading.Lock()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps(self.database).encode('utf-8')
        self.wfile.write(response)

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        with self.lock:
            for key, value in data.items():
                if key not in self.database:
                    self.database[key] = {}

                self.database[key].update(value)

        self.rfile.write(json.dumps({'status': 'success'}).encode('utf-8'))

    def get_keywords(self) -> List[str]:
        with self.lock:
            return list(self.database.get('keywords', {}).keys())

server_address = (LOCALHOST, PORT)
server = HTTPServer(server_address, DatabaseManager)

print(f'Server started at http://{LOCALHOST}:{PORT}')
server.serve_forever()
server.server_close()
