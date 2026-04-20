from math import sqrt
import asyncio
import sys
import socket

def sqroots(coeffs: str) -> str:
    a, b, c = map(int, coeffs.split())

    D = b**2 - 4 * a * c
    
    if D > 0:
        return ' '.join([ str((-b - sqrt(D))/(2*a)), str((-b + sqrt(D))/(2*a)) ])
    
    if D == 0:
        return str( -b/(2*a) )

    return ''

def srv_sqroots(coeffs: str) -> str:
    try:
        a, b, c = map(int, coeffs.split())

        D = b**2 - 4 * a * c

        if D > 0:
            return ' '.join([ str((-b - sqrt(D))/(2*a)), str((-b + sqrt(D))/(2*a)) ])

        if D == 0:
            return str( -b/(2*a) )
    except Exception as E:
        pass

    return ''

async def echo(reader, writer):
    writer.write((srv_sqroots((await reader.readline()).strip().decode()) + '\n').encode())
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(echo, '0.0.0.0', 1337)
    async with server:
        await server.serve_forever()

def sqrootnet(coeffs: str, s: socket.socket) -> str:
    s.sendall((coeffs + "\n").encode())
    return s.recv(128).decode().strip()

def srv():
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        asyncio.run(main())
    elif len(sys.argv) > 1 and sys.argv[1] == 'client':
        host = "localhost"
        port = 1337
        coeffs = input('>')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print(sqrootnet(coeffs, s))

if __name__ == "__main__":
    srv()
