import threading
import hashlib
from node.file_manager import FileManager
from node.downloader import Downloader
from tests.mock_peer_server import MockPeerServer


def test_downloader_with_mock():
    pieces = {0: b"Piece 0 data", 1: b"Piece 1 data"}

    # Start the mock peer server
    server = MockPeerServer("127.0.0.1", 0, pieces)  # Port 0 for dynamic assignment
    server_thread = threading.Thread(target=server.start)
    server_thread.start()

    # Wait for the server to start and retrieve the correct port
    while not server.running:
        pass  # Wait until the server is running
    peer_port = server.port  # Get the actual port
    print(f"Mock Peer Server running on {server.host}:{peer_port}")

    # Ensure that the peer port is correct before proceeding
    if not peer_port:
        raise ValueError("Failed to get a valid port for the server.")

    # Use the correct port in the peers list
    peers = [{"ip": server.host, "port": peer_port}]

    # Define the other test setup
    output_file = "downloaded_file.txt"
    piece_hashes = {
        index: hashlib.sha1(piece).hexdigest() for index, piece in pieces.items()
    }
    file_manager = FileManager(
        piece_size=512 * 1024, piece_hashes=piece_hashes
    )  # Use default piece size or specify

    # Run the downloader
    downloader = Downloader(file_manager, piece_hashes, peers, output_file)
    downloader.start_download()

    # Validate the result
    with open(output_file, "rb") as f:
        downloaded_data = f.read()
    expected_data = b"".join(pieces.values())

    assert (
        downloaded_data == expected_data
    ), f"Downloaded data does not match! Expected: {expected_data}, Got: {downloaded_data}"


if __name__ == "__main__":
    test_downloader_with_mock()
