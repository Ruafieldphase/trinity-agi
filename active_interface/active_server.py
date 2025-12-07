import http.server
import socketserver
import json
import os
import sys

# Set port
PORT = 3005

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')
JSON_FILE = os.path.join(OUTPUTS_DIR, 'active_context.json')

class ActiveContextHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve active_context.json for root or specific path
        if self.path == '/' or self.path == '/active_context.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Allow CORS for dashboard
            self.end_headers()
            
            if os.path.exists(JSON_FILE):
                try:
                    with open(JSON_FILE, 'rb') as f:
                        self.wfile.write(f.read())
                except Exception as e:
                    error_msg = json.dumps({"error": str(e)}).encode('utf-8')
                    self.wfile.write(error_msg)
            else:
                # Return empty JSON if file doesn't exist yet
                self.wfile.write(b'{"status": "waiting_for_context", "message": "active_context.json not found"}')
        else:
            # Default 404 for other paths
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def log_message(self, format, *args):
        # Override to print to stdout (which goes to log file)
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format%args))

print(f"Starting Active Trinity Server on port {PORT}...")
print(f"Serving file: {JSON_FILE}")

# Allow address reuse to prevent "Address already in use" errors on restart
socketserver.TCPServer.allow_reuse_address = True

try:
    with socketserver.TCPServer(("", PORT), ActiveContextHandler) as httpd:
        print(f"Serving forever at http://localhost:{PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server...")
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)
