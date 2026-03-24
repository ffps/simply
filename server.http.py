#!/usr/bin/python3

import http.server
import socketserver

PORT = 8088


class RequestHandler(http.server.BaseHTTPRequestHandler):
    """Simplest http server for debug incoming requests"""

    def do_GET(self):
        self.response()

    def do_POST(self):
        self.response()

    def do_PUT(self):
        self.response()

    def do_DELETE(self):
        self.response()

    def log_request(self, code=None, size=None):
        peer = self.connection.getpeername()
        headers = [f"    {key}: {val}" for key, val in self.headers.items()] if hasattr(self, "headers") else []

        c_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(c_len).decode("utf-8", errors="replace") if c_len else ""

        self.log = [f"{self.requestline}", f"  CLIENT: {peer[0]}:{peer[1]}", "  HEADERS:"] + headers
        self.log += [f"  BODY:{repr(body)}"]
        self.log = "\n".join(self.log)

    def response(self):
        q = self.path.strip("/")
        self.status = (int(q), f"ERROR {q}") if q.isdigit() else (200, "OK")
        self.send_response(*self.status)
        self.send_header("Content-type", "text/plain")
        self.response_headers = b"\n  RESPONSE:\n    HEADERS:\n      " + b"      ".join(self._headers_buffer)
        self.end_headers()
        self.wfile.write(self.log.encode())
        self.wfile.write(self.response_headers)
        print(self.log)
        print(self.response_headers.decode())


with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
    print(f"HTTP Server started at port {PORT}")
    httpd.serve_forever()
