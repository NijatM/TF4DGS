"""Serve only the textile documentation locally, with MP4 byte-range support."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'documentation/dynamic_textile_001'


class Handler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'

    def send_head(self):
        self.byte_range=None
        path=Path(self.translate_path(self.path)).resolve()
        # Keep the local server inside this documentation directory.
        if path!=DOCS and DOCS not in path.parents:
            self.send_error(403);return None
        request=self.headers.get('Range')
        if not request or not path.is_file():return super().send_head()
        size=path.stat().st_size;match=re.fullmatch(r'bytes=(\d*)-(\d*)',request.strip())
        if not match or not size or not any(match.groups()):
            self.send_error(416,'Unsupported byte range');return None
        lo,hi=match.groups()
        if lo:
            start=int(lo);end=min(int(hi),size-1) if hi else size-1
        else:
            length=int(hi);start=max(0,size-length);end=size-1
            if length<=0:start=size
        if start>=size or end<start:
            self.send_response(416);self.send_header('Content-Range',f'bytes */{size}')
            self.send_header('Content-Length','0');self.end_headers();return None
        stream=path.open('rb');stream.seek(start);self.byte_range=(start,end)
        self.send_response(206);self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length',str(end-start+1))
        self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime));self.end_headers()
        return stream

    def end_headers(self):
        self.send_header('Accept-Ranges','bytes');self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()

    def copyfile(self,source,outputfile):
        if self.byte_range is None:return super().copyfile(source,outputfile)
        remaining=self.byte_range[1]-self.byte_range[0]+1
        while remaining:
            data=source.read(min(65536,remaining))
            if not data:break
            outputfile.write(data);remaining-=len(data)

    def log_message(self,*args):pass


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8105);a=parser.parse_args()
    assert a.port==8105,'Use the dedicated textile documentation port'
    print('Textile documentation and seekable videos: http://127.0.0.1:8105/videos/',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(DOCS))).serve_forever()


if __name__=='__main__':main()
