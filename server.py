"""Local-only HTTP entry point. No remote access, credentials or external writes."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from engine import analyze

MAX_BODY = 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.respond(200, {'status': 'UP'}) if self.path == '/health' else self.respond(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path != '/api/v1/impact':
            return self.respond(404, {'error': 'Not found'})
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            return self.respond(415, {'error': 'Use application/json'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size <= 0:
                raise ValueError('A JSON body is required')
            if size > MAX_BODY:
                return self.respond(413, {'error': 'Body exceeds 1 MiB'})
            result = analyze(json.loads(self.rfile.read(size)))
        except (ValueError, UnicodeError) as exc:
            return self.respond(400, {'error': str(exc)})
        self.respond(200, result)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8080), Handler)
    server.timeout = 10
    print('ChangeGuard API: http://127.0.0.1:8080', flush=True)
    server.serve_forever()
