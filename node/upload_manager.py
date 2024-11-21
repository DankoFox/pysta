import socket
import threading
from node.file_manager import FileManager


class UploadManager:
    def __init__(self, host, port, file_manager: FileManager, file_path):
        """
        Initialize the UploadManager.
        :param host: Host IP address to bind the server.
        :param port: Port to bind the server.
        :param file_manager: Instance of FileManager to retrieve file pieces.
        :param file_path: Path to the file being managed by this UploadManager.
        """
        self.host = host
        self.port = port
        self.file_manager = file_manager
        self.file_path = file_path  # File being managed by this UploadManager
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def start_server(self):
        """
        Start the upload server to handle incoming peer requests.
        """
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(
                f"UploadManager running on {self.host}:{self.port}, serving file: {self.file_path}"
            )

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
        """
        Handle incoming requests from peers.
        :param client_socket: Socket of the connected peer.
        """
        try:
            request = client_socket.recv(1024).decode().strip()
            if request.startswith("GET_PIECE"):
                _, piece_index = request.split()
                piece_index = int(piece_index)
                piece_data = self.file_manager.get_piece(piece_index, self.file_path)

                if piece_data:
                    client_socket.sendall(piece_data)
                    print(f"Sent piece {piece_index} to peer.")
                else:
                    client_socket.sendall(b"ERROR: Piece not found.")

            else:
                client_socket.sendall(b"ERROR: Invalid request.")
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            client_socket.close()


# if __name__ == "__main__":
#     file_path = "path/to/your/file.txt"  # Specify the file path here
#     file_manager = FileManager(piece_size=512 * 1024, piece_hashes={})
#     file_manager.split_file(file_path)  # Split the file and populate piece hashes
#     upload_manager = UploadManager("127.0.0.1", 5000, file_manager, file_path)
#
#     try:
#         upload_manager.start_server()
#     except KeyboardInterrupt:
#         upload_manager.stop_server()
