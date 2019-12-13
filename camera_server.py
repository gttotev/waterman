#!/usr/bin/env python3

import io
import picamera
import logman
import logging
import socketserver
from threading import Condition
from http import server

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
<script>
function sendReq(text) {
    var oReq = new XMLHttpRequest();
    oReq.open("GET", "/" + text);
    oReq.send();
}
</script>
</head>
<body>
<h1>PiCamera MJPEG Streaming Demo</h1>
<a href="/log" target="_blank">LOG</a>
<button onclick="sendReq('clear_log')">Clear</button>
<br />
<img src="stream.mjpg" width="640" height="480" />
<h3>Water</h3>
<button onclick="sendReq('start_pump=0')">0</button>
<button onclick="sendReq('start_pump=1')">1</button>
<button onclick="sendReq('start_pump=2')">2</button>
<h3>Other actions</h3>
<button onclick="sendReq('stop')">STOP</button>
<button onclick="sendReq('disable')">DISABLE</button>
<button onclick="sendReq('enable')">ENABLE</button>
</body>
</html>
"""

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

mq = []

class StreamingHandler(server.BaseHTTPRequestHandler):
    output = None
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/log':
            with open(logman.LOG_PATH) as logfile:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(logfile.read().encode())
        elif self.path == '/clear_log':
            logman.clear_log()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK\r\n')
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
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
        else:
            global mq
            mq.append(self.path[1:])
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK\r\n')

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def serve():
    #with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    with picamera.PiCamera(resolution='1296x972', framerate=30) as camera:
    #with picamera.PiCamera(resolution='2592x1944', framerate=15) as camera:
        output = StreamingOutput()
        StreamingHandler.output = output
        camera.start_recording(output, format='mjpeg')
        try:
            address = ('', 8000)
            server = StreamingServer(address, StreamingHandler)
            logman.log('camera_server: Server created!')
            server.serve_forever()
        finally:
            camera.stop_recording()

if __name__ == '__main__':
    serve()
