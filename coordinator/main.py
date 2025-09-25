import http.server
import socketserver
import json
import logging

PORT = 5000
LOG_FILE = 'coordinator.log'

# Configure logging to write directly to a file
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/v1/results':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                logging.info("--- REQUEST RECEIVED ---")

                # Parse and log the JSON data
                data = json.loads(post_data)
                logging.info("Received data from agent:")
                logging.info(json.dumps(data, indent=2))

                # Send response
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'success', 'message': 'Data received'}
                self.wfile.write(json.dumps(response).encode('utf-8'))

                logging.info("--- RESPONSE SENT ---")

            except Exception as e:
                logging.error(f"Error processing request: {e}")
                self.send_response(500)
                self.end_headers()
                response = {'status': 'error', 'message': 'Internal server error'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            response = {'status': 'error', 'message': 'Not Found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        # Silence non-POST requests
        self.send_response(405)
        self.end_headers()
        self.wfile.write(b'Method Not Allowed')

with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
    logging.info(f"Coordinator server starting on port {PORT}")
    print(f"serving at port {PORT}")
    httpd.serve_forever()