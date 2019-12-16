#!/usr/bin/env python3

import picamera, logman, os
import io, logging, socketserver
from threading import Condition
from http import server

INDEX_PATH = os.path.join(os.path.dirname(__file__), 'index.html')

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    output = StreamingOutput()
    other_handler = lambda cls, path: None

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open(INDEX_PATH) as f:
                self.wfile.write(f.read().encode())

        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with self.output.condition:
                        self.output.condition.wait()
                        frame = self.output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))

        elif self.path == '/log':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(logman.dump().encode())
        elif self.path == '/clear_log':
            logman.clear_log()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK\r\n')

        else:
            res = self.other_handler(self.path)
            self.send_response(res[0])
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(res[1].encode())

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def serve(other_handler=lambda cls, x: None):
    with picamera.PiCamera(resolution='1296x972', framerate=30) as camera:
        StreamingHandler.other_handler = other_handler
        camera.start_recording(StreamingHandler.output, format='mjpeg')
        try:
            address = ('', 8000)
            server = StreamingServer(address, StreamingHandler)
            logman.log('camera_server: Server created!')
            server.serve_forever()
        finally:
            camera.stop_recording()

if __name__ == '__main__':
    serve()
