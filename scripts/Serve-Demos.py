"""Serve only the final demo gallery on localhost, with seekable MP4 playback."""
from functools import partial
from http.server import ThreadingHTTPServer
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    server = SourceFileLoader('tf4dgs_demo_http', str(
        ROOT / 'scripts/Serve-TextileDocumentation.py')).load_module()
    server.DOCS = ROOT / 'documentation/demos'
    if not (server.DOCS / 'index.html').is_file():
        raise FileNotFoundError('Build the demo gallery first')
    print('TF4DGS demos: http://127.0.0.1:8107/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8107), partial(
        server.Handler, directory=str(server.DOCS))).serve_forever()


if __name__ == '__main__':
    main()
