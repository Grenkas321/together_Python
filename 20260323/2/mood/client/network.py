"""Networking helpers for the MOOD client."""

import json
import queue
import socket
import threading

from mood.common.constants import DEFAULT_HOST, DEFAULT_PORT, SHELL_PROMPT
from mood.common.protocol import Payload, error_response


class NetworkClient:
    """Talk to a MOOD server over TCP."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.sock = socket.create_connection((host, port))
        self.reader = self.sock.makefile("r", encoding="utf-8")
        self.writer = self.sock.makefile("w", encoding="utf-8")
        self.responses: queue.Queue[Payload] = queue.Queue()
        self.closed = False
        self.listener = threading.Thread(target=self._reader_loop, daemon=True)
        self.listener.start()

    def _reader_loop(self) -> None:
        while not self.closed:
            try:
                response_line = self.reader.readline()
            except OSError:
                if not self.closed:
                    self.responses.put(error_response("Server disconnected"))
                return

            if not response_line:
                self.responses.put(error_response("Server disconnected"))
                return

            try:
                response = json.loads(response_line)
            except json.JSONDecodeError:
                self.responses.put(error_response("Invalid server response"))
                continue

            if response.get("type") == "sayall" and "from" in response:
                print(f"\n{response['from']}: {response['message']}")
                print(SHELL_PROMPT, end="", flush=True)
                continue

            self.responses.put(response)

    def request(self, line: str) -> Payload:
        """Send a request to the server and wait for the response."""
        try:
            self.writer.write(line + "\n")
            self.writer.flush()
        except OSError:
            return error_response("Failed to send request")
        return self.responses.get()

    def close(self) -> None:
        """Close the client connection and release resources."""
        if self.closed:
            return
        self.closed = True
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.reader.close()
        except OSError:
            pass
        try:
            self.writer.close()
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass
