from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
def main():
    return {'ok': True, 'note': 'scaffold only — not a long-running server claim'}
if __name__ == '__main__':
    print(main())
