import socket


class MockPeerServer:
    def __init__(self, host, port, pieces):
        self.host = host
        self.port = port
        self.pieces = pieces
        self.server_socket = None
        self.running = False

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.port = self.server_socket.getsockname()[
                1
            ]  # Get dynamically assigned port
            self.running = True
            print(f"Server started on {self.host}:{self.port}")

            while self.running:
                client_socket, client_address = self.server_socket.accept()
                self.handle_client(client_socket)

        except Exception as e:
            print(f"Error starting server: {e}")

    def handle_client(self, client_socket):
        try:
            request = client_socket.recv(1024).decode()
            if request.startswith("GET_PIECE"):
                piece_index = int(request.split()[1])
                piece_data = self.pieces.get(piece_index, b"")
                client_socket.sendall(piece_data)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
