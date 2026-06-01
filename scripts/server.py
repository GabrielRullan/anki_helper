import os
import json
import csv
from http.server import SimpleHTTPRequestHandler, HTTPServer
from generate_dashboard import generate_dashboard

PORT = 8000

import os
# Change working directory to root
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve dashboard.html by default at root path
        if self.path == '/' or self.path == '/index.html':
            self.path = '/dashboard.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/known_characters':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                character = data.get('character', '').strip()
                
                if not character:
                    self._send_json({"status": "error", "message": "No character provided"}, 400)
                    return
                
                # Write to known_characters.csv
                csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_characters.csv"))
                
                # Read existing characters to avoid duplicates
                existing_chars = []
                if os.path.exists(csv_path):
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader, None) # skip header
                        for row in reader:
                            if row and row[0].strip():
                                val = row[0].strip()
                                if val not in existing_chars:
                                    existing_chars.append(val)
                                
                if character not in existing_chars:
                    existing_chars.append(character)
                    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Character'])
                        for char in existing_chars:
                            writer.writerow([char])
                
                # Re-generate the dashboard HTML file
                print(f"Regenerating dashboard after marking '{character}' as known...")
                generate_dashboard()
                
                self._send_json({"status": "success", "character": character})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
        elif self.path == '/api/known_words':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                word = data.get('word', '').strip()
                
                if not word:
                    self._send_json({"status": "error", "message": "No word provided"}, 400)
                    return
                
                # Write to known_words.csv
                csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_words.csv"))
                
                # Read existing words to avoid duplicates
                existing_words = []
                if os.path.exists(csv_path):
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader, None) # skip header
                        for row in reader:
                            if row and row[0].strip():
                                val = row[0].strip()
                                if val not in existing_words:
                                    existing_words.append(val)
                                
                if word not in existing_words:
                    existing_words.append(word)
                    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Word'])
                        for w in existing_words:
                            writer.writerow([w])
                
                # Re-generate the dashboard HTML file
                print(f"Regenerating dashboard after marking word '{word}' as known...")
                generate_dashboard()
                
                self._send_json({"status": "success", "word": word})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
        else:
            self.send_error(404, "Not Found")

    def _send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        # Support CORS for development/local file setups
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print(f"Anki Paladin Dashboard Server running at http://localhost:{PORT}/")
    print(f"Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run()
