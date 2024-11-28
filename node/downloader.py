import socket
import threading
from node.file_manager import FileManager


class Downloader:
    def __init__(self, file_manager, piece_hashes, peers, output_path):
        """
        Initialize the Downloader.
        :param file_manager: Instance of FileManager to handle file operations.
        :param piece_hashes: Dictionary of piece indices and their hashes.
        :param peers: List of peers (dictionaries with 'ip' and 'port').
        :param output_path: Path to save the downloaded file.
        """
        if not peers:
            raise ValueError("At least one peer is required for downloading.")

        self.file_manager = file_manager
        self.piece_hashes = piece_hashes
        self.peers = peers
        self.output_path = output_path
        self.piece_size = file_manager.piece_size
        self.pieces_downloaded = {}
        self.lock = threading.Lock()

    def start_download(self):
        """
        Start downloading pieces from peers.
        """
        threads = []
        for piece_index in range(len(self.piece_hashes)):
            peer = self.peers[
                piece_index % len(self.peers)
            ]  # Simple round-robin peer selection
            thread = threading.Thread(
                target=self.download_piece, args=(peer, piece_index)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
            
        # Merge pieces into the output file
        self.file_manager.merge_pieces(self.pieces_downloaded, self.output_path)
        print(f"Download complete. File saved to {self.output_path}.")

    def download_piece(self, peer, piece_index):
        """
        Download a single piece from a peer.
        :param peer: Dictionary with 'ip' and 'port'.
        :param piece_index: Index of the piece to download.
        """
        try:
            with socket.create_connection((peer["ip"], peer["port"])) as s:
                # Send request for the piece
                request = f"GET_PIECE {piece_index}\n"
                s.sendall(request.encode())

                # Receive the piece data
                piece_data = b""
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    piece_data += chunk

                # Verify the piece hash
                piece_hash = FileManager.hash_piece(piece_data)
                if piece_hash != self.piece_hashes[piece_index]:
                    print(f"Hash mismatch for piece {piece_index}.")
                    return

                # Save the piece
                with self.lock:
                    self.pieces_downloaded[piece_index] = piece_data
                    print(
                        f"Downloaded piece {piece_index} from {peer['ip']}:{peer['port']}"
                    )
        except socket.error as e:
            print(
                f"Failed to download piece {piece_index} from {peer['ip']}:{peer['port']}: {e}"
            )
        except Exception as e:
            print(f"An error occurred while downloading piece {piece_index}: {e}")
