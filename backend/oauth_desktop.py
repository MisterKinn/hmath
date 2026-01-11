import webbrowser
import http.server
import socketserver
import threading
import json
import os
import time
from urllib.parse import urlparse, parse_qs, unquote

CALLBACK_PORT = 8765
CALLBACK_PATH = "/auth-callback"
USER_DATA_FILE = os.path.join(os.path.dirname(__file__), "user_account.json")
CALLBACK_TIMEOUT = 300  # 5 minutes

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "OAuthCallbackHandler/1.0"
    def do_GET(self):
        if self.path.startswith(CALLBACK_PATH):
            query = urlparse(self.path).query
            params = parse_qs(query)
            # URL-decode and flatten
            user_data = {k: unquote(v[0]) for k, v in params.items()}
            # Validate required fields
            if not user_data.get("uid") or not user_data.get("email"):
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>Login failed: missing required fields.</h1>")
                self.server._login_result = False
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            # Store user info
            with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Login successful. You can close this window.</h1>")
            self.server._login_result = True
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_error(404)

def start_oauth_flow():
    # Remove any previous user data
    if os.path.exists(USER_DATA_FILE):
        os.remove(USER_DATA_FILE)
    handler = OAuthCallbackHandler
    httpd = socketserver.TCPServer(("", CALLBACK_PORT), handler)
    httpd._login_result = None
    # Start server in a thread
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    # Open browser to login page with redirect_uri
    login_url = f"http://localhost:3000/login?redirect_uri=http://localhost:{CALLBACK_PORT}{CALLBACK_PATH}"
    webbrowser.open(login_url)
    print(f"Opened browser for login: {login_url}")
    print("Waiting for login callback (timeout: %ds)..." % CALLBACK_TIMEOUT)
    start_time = time.time()
    while httpd._login_result is None and (time.time() - start_time) < CALLBACK_TIMEOUT:
        time.sleep(0.5)
    if httpd._login_result:
        print("Login complete.")
    elif httpd._login_result is False:
        print("Login failed: missing required fields.")
    else:
        print("Login timed out.")
        httpd.shutdown()

def get_stored_user():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
