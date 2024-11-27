import socket
import threading
from node.file_manager import FileManager
from node.upload_manager import UploadManager


def run_upload_manager():
    """
    Start the UploadManager in a separate thread.
    """
    file_manager = FileManager()

    # Split and store files for testing
    file_manager.split_file("file1.txt", piece_size=20)

    file_manager.split_file("file2.txt", piece_size=512)
    print("Metadata:", file_manager.get_metadata("file2.txt"))
    print("Piece 0:", file_manager.get_piece(0, "file2.txt"))

    upload_manager = UploadManager("127.0.0.1", 5000, file_manager)

    # Run the server in a thread to allow client testing
    thread = threading.Thread(target=upload_manager.start_server, daemon=True)
    thread.start()
    return upload_manager


def test_upload_manager():
    """
    Test the UploadManager by sending requests for file pieces and metadata.
    """
    # Start the UploadManager
    upload_manager = run_upload_manager()

    try:
        # Connect to the server as a mock client
        with socket.create_connection(("127.0.0.1", 5000)) as client_socket:
            # Test GET_METADATA request
            client_socket.sendall(b"GET_METADATA file1.txt")
            metadata_response = client_socket.recv(4096).decode()
            print("Metadata response for file1.txt:", metadata_response)

            # Test GET_PIECE request (valid piece index)
            client_socket.sendall(b"GET_PIECE file1.txt 0")
            piece_response = client_socket.recv(4096)
            print("Piece 0 of file1.txt:", piece_response)

            # Test GET_PIECE request (invalid piece index)
            client_socket.sendall(b"GET_PIECE file1.txt 100")
            error_response = client_socket.recv(4096).decode()
            print("Error response for invalid piece index:", error_response)

            # Test GET_PIECE request for non-existent file
            client_socket.sendall(b"GET_PIECE nonexistent.txt 0")
            nonexistent_response = client_socket.recv(4096).decode()
            print("Error response for non-existent file:", nonexistent_response)

    finally:
        # Stop the server after testing
        upload_manager.stop_server()


if __name__ == "__main__":
    test_upload_manager()
