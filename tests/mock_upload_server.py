import threading
import socket


class MockUploadServer:
    def __init__(self, host, port, file_content, piece_size):
        self.host = host
        self.port = port
        self.file_content = (
            file_content * 10
        )  # Simulate larger file content by repeating it
        self.piece_size = piece_size
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"MockUploadServer running on {self.host}:{self.port}")
        threading.Thread(target=self.handle_connections, daemon=True).start()

    def handle_connections(self):
        while self.running:
            client_socket, _ = self.server_socket.accept()
            threading.Thread(
                target=self.handle_client, args=(client_socket,), daemon=True
            ).start()

    def handle_client(self, client_socket):
        try:
            while True:
                request = client_socket.recv(1024).decode().strip()
                if not request:
                    break

                if request.startswith("GET_PIECE"):
                    parts = request.split()
                    if len(parts) != 2:
                        client_socket.sendall(b"ERROR: Invalid request.")
                        continue

                    _, piece_index = parts
                    piece_index = int(piece_index)
                    start = piece_index * self.piece_size
                    end = min(start + self.piece_size, len(self.file_content))

                    if 0 <= start < len(self.file_content):
                        piece_data = self.file_content[start:end]
                        client_socket.sendall(piece_data)
                        print(
                            f"[[MOCK-SERVER]] :: Calculating piece range for index {piece_index}"
                        )
                        print(
                            f"[[MOCK-SERVER]] :: File length: {len(self.file_content)}, Piece size: {self.piece_size}"
                        )
                        print(f"[[MOCK-SERVER]] :: Start: {start}, End: {end}")
                        print(
                            f"[[MOCK-SEVER]] :: Serving piece {piece_index}, expected size: {self.piece_size}, actual size: {len(piece_data)}"
                        )
                    else:
                        client_socket.sendall(b"ERROR: Piece not found.")
                else:
                    client_socket.sendall(b"ERROR: Invalid request.")
        except Exception as e:
            print(f"Exception in handle_client: {e}")
        finally:
            client_socket.close()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            print(f"MockUploadServer stopped.")
