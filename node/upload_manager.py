import socket
import threading
from node.file_manager import FileManager


class UploadManager:
    def __init__(self, host, port, file_manager: FileManager):
        """
        Initialize the UploadManager.
        :param host: Host IP address to bind the server.
        :param port: Port to bind the server.
        :param file_manager: Instance of FileManager to retrieve file pieces and metadata.
        """
        self.host = host
        self.port = port
        self.file_manager = file_manager
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        buffer_size = 10 * 1024 * 1024  # 10 MB
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_size)

        self.running = False

    def start_server(self):
        """
        Start the upload server to handle incoming peer requests.
        """
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"UploadManager running on {self.host}:{self.port}")

            while self.running:
                client_socket, client_address = self.server_socket.accept()
                print(f"Connection established with {client_address}")
                threading.Thread(
                    target=self.handle_request, args=(client_socket,)
                ).start()
        except Exception as e:
            print(f"Error starting server: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """
        Stop the upload server.
        """
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("UploadManager stopped.")

    def handle_request(self, client_socket):
        try:
            # print("Metadata in FileManager at start:", self.file_manager.get_all_info())
            while True:
                # file_manager.get_all_info()
                request = client_socket.recv(1024).decode().strip()
                if not request:
                    break  # Close connection if the client sends no data
                print(f"Received request: {request}")

                if request.startswith("GET_METADATA"):
                    _, file_name = request.split()
                    metadata = self.file_manager.get_metadata(file_name)
                    if metadata:
                        client_socket.sendall(str(metadata).encode())
                        print(f"Sent metadata of {file_name} to peer.")
                    else:
                        client_socket.sendall(b"ERROR: Metadata not found.")

                elif request.startswith("GET_PIECE"):
                    _, file_name, piece_index = request.split()
                    # print(self.file_manager.get_all_info())
                    piece_index = int(piece_index)
                    piece_data = self.file_manager.get_piece(piece_index, file_name)
                    # print(f"Sending piece {piece_index}: {piece_data}")

                    if piece_data:
                        client_socket.sendall(piece_data)
                        print(f"Sent piece {piece_index} of {file_name} to peer.")
                    else:
                        client_socket.sendall(b"ERROR: Piece not found.")

                elif request == "QUIT":
                    print("Client requested to close the connection.")
                    break

                else:
                    client_socket.sendall(b"ERROR: Invalid request.")
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            client_socket.close()
