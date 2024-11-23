import os
import socket
import hashlib
import time


class DownloadManager:
    def __init__(self, file_path, piece_size, piece_hashes, file_size, max_retries=3):
        """
        Initialize the DownloadManager.

        :param file_path: Path to save the downloaded file.
        :param piece_size: Size of each piece in bytes.
        :param piece_hashes: List of hashes for each piece.
        :param max_retries: Maximum number of retries for downloading a piece.
        """
        self.file_path = file_path
        self.piece_size = piece_size
        self.piece_hashes = piece_hashes
        self.file_size = file_size
        self.pieces_received = [False] * len(piece_hashes)  # Track downloaded pieces
        self.max_retries = max_retries

        # Pre-truncate the file to full size
        with open(self.file_path, "wb") as f:
            f.write(b"\x00" * self.file_size)
        print(f"File initialized to {self.file_size} bytes with placeholders.")

    def connect_to_peer(self, peer_address):
        """
        Establish a connection to a peer.

        :param peer_address: Tuple of (IP, port) to connect to.
        :return: A connected socket object.
        """
        sock = socket.create_connection(peer_address)
        print(f"Connected to peer at {peer_address}")
        return sock

    def request_piece(self, sock, piece_index):
        """
        Request a specific piece from the peer.

        :param sock: The socket connected to the peer.
        :param piece_index: Index of the piece to request.
        :return: The received piece data.
        """

        print("\n============++++++")
        print(f"FILE LENGTH: {self.file_size}\n")
        retries = 0

        # Calculate the correct size for the requested piece
        start_offset = piece_index * self.piece_size
        is_last_piece = piece_index == len(self.piece_hashes) - 1
        piece_size = (
            (self.file_size - start_offset) if is_last_piece else self.piece_size
        )

        if piece_size < 0:
            piece_size = 0

        print(f"THIS IS THE PIECE SIZE CALCULATION: {piece_size}")

        while retries < self.max_retries:
            try:
                sock.sendall(f"GET_PIECE {piece_index}\n".encode())
                piece_data = sock.recv(piece_size)  # Request correct size

                print(f"Received piece {piece_index} from peer.")
                print("=DEBUG=======================================================")
                print(f"Requested piece {piece_index}, expected size: {piece_size}")
                print(f"Received piece size: {len(piece_data)}")
                print("=DEBUG=======================================================")

                return piece_data
            except (BrokenPipeError, ConnectionError) as e:
                print(f"Error requesting piece {piece_index}: {e}. Retrying...")
                retries += 1
                sock = self.connect_to_peer(sock.getpeername())  # Reconnect to peer
        raise ConnectionError(
            f"Failed to retrieve piece {piece_index} after {self.max_retries} attempts"
        )

    def verify_piece(self, piece_data, piece_index):
        """
        Verify the integrity of a piece using its hash.

        :param piece_data: The data of the piece.
        :param piece_index: Index of the piece.
        :return: True if the piece is valid, False otherwise.
        """
        expected_hash = self.piece_hashes[piece_index]
        actual_hash = hashlib.sha256(piece_data).hexdigest()

        print(f"Expected hash for piece {piece_index}: {expected_hash}")
        print(f"Actual hash for piece {piece_index}: {actual_hash}")

        is_valid = expected_hash == actual_hash
        if not is_valid:
            print(f"Piece {piece_index} failed verification.")
        return is_valid

    def write_piece_to_file(self, piece_index, piece_data):
        """
        Write a verified piece to the correct position in the file.

        :param piece_index: Index of the piece.
        :param piece_data: The data of the piece.
        """
        offset = piece_index * self.piece_size
        with open(self.file_path, "r+b") as f:
            f.seek(offset)
            f.write(piece_data)
        self.pieces_received[piece_index] = True
        print(f"Piece {piece_index} written to file at offset {offset}.")

    def start_download(self, peer_address):
        """
        Start the download process from a peer.

        :param peer_address: Tuple of (IP, port) of the peer.
        """
        try:
            sock = self.connect_to_peer(peer_address)
            for piece_index in range(len(self.piece_hashes)):
                piece_data = self.request_piece(sock, piece_index)
                if self.verify_piece(piece_data, piece_index):
                    self.write_piece_to_file(piece_index, piece_data)
                else:
                    print(f"Invalid piece {piece_index} left as placeholder.")
                time.sleep(0.01)  # Add a short delay to avoid overloading the server
            print(f"Download complete. File saved at {self.file_path}")
        finally:
            print("DownloadManager stopped.")
