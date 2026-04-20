def sqrootnet(coeffs: str, s: socket.socket) -> str:
    s.sendall((coeffs + "\n").encode())
    return s.recv(128).decode().strip()