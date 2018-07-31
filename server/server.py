import sys
import os
import time
import SocketServer
import SimpleHTTPServer

if len(sys.argv) < 2:
    print "Needs one argument: server port"
    raise SystemExit

PORT = int(sys.argv[1])

class HTTPCacheRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def send_head(self):
        if self.command != "POST" and self.headers.get('If-Modified-Since', None):
            filename = self.path.strip("/")
	    print filename
            if os.path.isfile(filename):
		y = time.gmtime(os.path.getmtime(filename))
#		print y, " File time"
		a = y
#Mon Feb 12 09:39:20 2018
                b = time.strptime(self.headers.get('If-Modified-Since', None), "%a %b %d %H:%M:%S %Y")
#		print b, " Cache time"
                if a <= b:
                    self.send_response(304)
                    self.end_headers()
                    return None
        return SimpleHTTPServer.SimpleHTTPRequestHandler.send_head(self)

    def end_headers(self):
        filename = self.path.strip("/")
        if filename[2] == "d":
            self.send_header('Cache-control', 'no-cache')
        else:
            self.send_header('Cache-control', 'must-revalidate')
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)

s = SocketServer.ThreadingTCPServer(("", PORT), HTTPCacheRequestHandler)
s.allow_reuse_address = True
print "Serving on port", PORT
s.serve_forever()
