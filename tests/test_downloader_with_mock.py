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


def test_downloader_multiple_pieces():
    pieces = {
        0: b"Piece 0 data",
        1: b"Piece 1 data",
        2: b"Piece 2 data",
        3: b"Piece 3 data",
    }

    # Start the mock peer server
    server = MockPeerServer("127.0.0.1", 0, pieces)
    server_thread = threading.Thread(target=server.start)
    server_thread.start()

    while not server.running:
        pass  # Wait until the server is running
    peer_port = server.port
    peers = [{"ip": server.host, "port": peer_port}]

    output_file = "downloaded_multiple_pieces.txt"
    piece_hashes = {
        index: hashlib.sha1(piece).hexdigest() for index, piece in pieces.items()
    }
    file_manager = FileManager(piece_size=512 * 1024, piece_hashes=piece_hashes)

    downloader = Downloader(file_manager, piece_hashes, peers, output_file)
    downloader.start_download()

    with open(output_file, "rb") as f:
        downloaded_data = f.read()
    expected_data = b"".join(pieces.values())

    assert (
        downloaded_data == expected_data
    ), f"Downloaded data does not match! Expected: {expected_data}, Got: {downloaded_data}"


def test_downloader_large_file():
    pieces = {i: f"Piece {i} data".encode() for i in range(100)}

    server = MockPeerServer("127.0.0.1", 0, pieces)
    server_thread = threading.Thread(target=server.start)
    server_thread.start()

    while not server.running:
        pass
    peer_port = server.port
    peers = [{"ip": server.host, "port": peer_port}]

    output_file = "downloaded_large_file.txt"
    piece_hashes = {
        index: hashlib.sha1(piece).hexdigest() for index, piece in pieces.items()
    }
    file_manager = FileManager(piece_size=512 * 1024, piece_hashes=piece_hashes)

    downloader = Downloader(file_manager, piece_hashes, peers, output_file)
    downloader.start_download()

    with open(output_file, "rb") as f:
        downloaded_data = f.read()
    expected_data = b"".join(pieces.values())

    assert (
        downloaded_data == expected_data
    ), f"Downloaded data does not match! Expected: {expected_data}, Got: {downloaded_data}"


###################


class CorruptedPieceServer(MockPeerServer):
    def __init__(self, host, port, pieces, corrupt_piece=None):
        """
        Initialize the server with the ability to corrupt a specific piece.
        :param corrupt_piece: Index of the piece to corrupt.
        """
        super().__init__(host, port, pieces)
        self.corrupt_piece = corrupt_piece

    def handle_request(self, client_socket):
        request = client_socket.recv(1024).decode().strip()
        if request.startswith("GET_PIECE"):
            piece_index = int(request.split()[1])
            if piece_index == self.corrupt_piece:
                print(f"Sending corrupted piece {piece_index}")
                corrupted_data = self.pieces[piece_index][::-1]  # Reverse to corrupt
                client_socket.sendall(corrupted_data)
            else:
                super().handle_request(client_socket)
        client_socket.close()


def test_downloader_with_corrupted_piece():
    pieces = {0: b"Piece 0 data", 1: b"Piece 1 data"}
    corrupted_piece_index = 1  # Corrupt the second piece

    # Start the corrupted piece server
    server = CorruptedPieceServer(
        "127.0.0.1", 0, pieces, corrupt_piece=corrupted_piece_index
    )
    server_thread = threading.Thread(target=server.start)
    server_thread.start()

    # Wait for the server to start
    while not server.running:
        pass
    peer_port = server.port
    print(f"Corrupted Peer Server running on {server.host}:{peer_port}")

    peers = [{"ip": server.host, "port": peer_port}]

    # Setup the downloader
    output_file = "downloaded_file_corrupted_piece.txt"
    piece_hashes = {
        index: hashlib.sha1(piece).hexdigest() for index, piece in pieces.items()
    }
    file_manager = FileManager(piece_size=512 * 1024, piece_hashes=piece_hashes)
    downloader = Downloader(file_manager, piece_hashes, peers, output_file)

    # Start the download
    downloader.start_download()

    # Validate the result
    with open(output_file, "rb") as f:
        downloaded_data = f.read()
    expected_data = b"".join(pieces.values())

    assert (
        downloaded_data == expected_data
    ), f"Downloaded data does not match! Expected: {expected_data}, Got: {downloaded_data}"


######################


class ConflictingPieceServer(MockPeerServer):
    def __init__(self, host, port, pieces, conflict_pieces):
        """
        Initialize the server with conflicting data for specific pieces.
        :param conflict_pieces: Dictionary of {piece_index: conflicting_data}.
        """
        super().__init__(host, port, pieces)
        self.conflict_pieces = conflict_pieces

    def handle_request(self, client_socket):
        request = client_socket.recv(1024).decode().strip()
        if request.startswith("GET_PIECE"):
            piece_index = int(request.split()[1])
            if piece_index in self.conflict_pieces:
                print(f"Sending conflicting data for piece {piece_index}")
                client_socket.sendall(self.conflict_pieces[piece_index])
            else:
                super().handle_request(client_socket)
        client_socket.close()


def test_downloader_with_conflicting_data():
    # Define valid and conflicting data
    pieces = {0: b"Piece 0 data", 1: b"Piece 1 data", 2: b"Ugly Good Bad"}
    conflict_pieces = {1: b"Corrupted Piece 1 data"}

    # Start a valid server
    valid_server = MockPeerServer("127.0.0.1", 0, pieces)
    valid_server_thread = threading.Thread(target=valid_server.start)
    valid_server_thread.start()

    # Start a conflicting server
    conflict_server = ConflictingPieceServer("127.0.0.1", 0, pieces, conflict_pieces)
    conflict_server_thread = threading.Thread(target=conflict_server.start)
    conflict_server_thread.start()

    # Wait for both servers to start
    while not valid_server.running or not conflict_server.running:
        pass
    valid_port = valid_server.port
    conflict_port = conflict_server.port

    print(f"Valid Peer Server running on {valid_server.host}:{valid_port}")
    print(f"Conflicting Peer Server running on {conflict_server.host}:{conflict_port}")

    # Configure peers
    peers = [
        {"ip": valid_server.host, "port": valid_port},
        {"ip": conflict_server.host, "port": conflict_port},
    ]

    # Setup the downloader
    output_file = "downloaded_file_conflicting_data.txt"
    piece_hashes = {
        index: hashlib.sha1(piece).hexdigest() for index, piece in pieces.items()
    }
    file_manager = FileManager(piece_size=512 * 1024, piece_hashes=piece_hashes)
    downloader = Downloader(file_manager, piece_hashes, peers, output_file)

    # Start the download
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
