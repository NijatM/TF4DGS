"""Local, read-only point-analysis preview; this does not render Gaussian splats."""
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .analysis import analyse, validate_tracks


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, tracks, **kwargs):
        self.tracks = tracks
        super().__init__(*args, **kwargs)

    def reply(self, body, content_type="application/json", code=200):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self.reply((Path(__file__).parent / "assets/preview.html").read_bytes(), "text/html; charset=utf-8")
            elif parsed.path == "/api/tracks":
                self.reply(json.dumps(self.tracks, allow_nan=False).encode())
            elif parsed.path == "/api/analysis":
                query = parse_qs(parsed.query)
                value = analyse(self.tracks, int(query.get("frame", ["0"])[0]),
                                query.get("mode", ["since_start"])[0], float(query.get("history", ["5"])[0]))
                self.reply(json.dumps(value, allow_nan=False).encode())
            elif parsed.path == "/api/health":
                self.reply(json.dumps({"project": "TF4DGS", "mode": "point_analysis", "synthetic": self.tracks.get("synthetic", False)}).encode())
            else:
                self.reply(b'{"error":"Not found"}', code=404)
        except (ValueError, KeyError, TypeError) as exc:
            self.reply(json.dumps({"error": str(exc)}).encode(), code=400)

    def log_message(self, *_):
        pass


def serve(tracks, port=8094):
    validate_tracks(tracks)
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, tracks=tracks))
    print(f"TF4DGS point preview: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
