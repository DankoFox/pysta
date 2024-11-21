import pytest
import os
import logging
import socket
import threading
import tempfile
from node.upload_manager import UploadManager
from node.file_manager import FileManager

# Initialize logging
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def setup_environment():
    # Find a free port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 0))
    free_port = server_socket.getsockname()[1]
    server_socket.close()

    # Create a temporary file with sample content
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(
            b"The more i I look into it, the more it stains onto my broken mind. At this state, sanity isn't of my possess anymore "
        )
        temp_file_path = temp_file.name
        print(f"Temporary file created: {temp_file_path}")

    # Set up FileManager
    piece_size = 10  # Small piece size for testing
    file_manager = FileManager(piece_size=piece_size, piece_hashes={})
    piece_hashes = file_manager.split_file(temp_file_path)  # Capture piece hashes

    # Update FileManager with correct piece_hashes
    file_manager.piece_hashes = piece_hashes

    # Set up UploadManager
    upload_manager = UploadManager("127.0.0.1", free_port, file_manager, temp_file_path)

    # Run UploadManager in a separate thread
    server_thread = threading.Thread(target=upload_manager.start_server, daemon=True)
    server_thread.start()

    yield upload_manager, temp_file_path, free_port

    # Ensure proper server shutdown
    upload_manager.stop_server()
    server_thread.join(timeout=2)  # Timeout after 2 seconds
    if server_thread.is_alive():
        logging.warning("Server thread did not terminate in time.")
    os.remove(temp_file_path)
    print("Temporary file removed and server stopped.")
    print("\n=========================================\n")


def test_valid_request(setup_environment):
    upload_manager, temp_file_path, free_port = setup_environment
    print("Starting test_valid_request")

    # Simulate a client sending a valid "GET_PIECE" request
    with socket.create_connection(("127.0.0.1", free_port)) as client_socket:
        client_socket.sendall(b"GET_PIECE 0\n")
        response = client_socket.recv(1024)
        print(f"Received response: {response}")

    # Verify the response matches the first piece of the file
    with open(temp_file_path, "rb") as f:
        expected_piece = f.read(upload_manager.file_manager.piece_size)
    assert response == expected_piece, f"Expected: {expected_piece}, Got: {response}"


def test_invalid_request(setup_environment):
    upload_manager, temp_file_path, free_port = setup_environment
    print("Starting test_invalid_request")

    # Simulate a client sending an invalid request
    with socket.create_connection(("127.0.0.1", free_port)) as client_socket:
        client_socket.sendall(b"INVALID_COMMAND\n")
        response = client_socket.recv(1024)
        print(f"Received response: {response}")

    # Verify the server responds with an error
    assert response == b"ERROR: Invalid request."


def test_nonexistent_piece_request(setup_environment):
    upload_manager, temp_file_path, free_port = setup_environment
    print("Starting test_nonexistent_piece_request")

    # Simulate a client requesting a non-existent piece
    with socket.create_connection(("127.0.0.1", free_port)) as client_socket:
        client_socket.sendall(b"GET_PIECE 999\n")
        response = client_socket.recv(1024)
        print(f"Received response: {response}")

    # Verify the server responds with an error
    assert response == b"ERROR: Piece not found."
