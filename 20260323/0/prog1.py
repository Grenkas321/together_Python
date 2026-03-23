import http.server
import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
print(s.getsockname()[0])
s.close()

http.server.test(http.server.SimpleHTTPRequestHandler, port = int(sys.argv[1]))