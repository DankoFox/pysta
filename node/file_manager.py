import hashlib
from threading import Lock


class FileManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FileManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.file_pieces = {}  # Dictionary to store pieces for multiple files
        self.file_metadata = {}  # Dictionary to store metadata for multiple files
        self.lock = Lock()  # Lock to ensure thread-safe access

    def split_file(self, file_path, piece_size):
        """
        Split a file into pieces and generate piece hashes.
        """
        with self.lock:
            with open(file_path, "rb") as f:
                content = f.read()

            pieces = [
                content[i : i + piece_size] for i in range(0, len(content), piece_size)
            ]
            piece_hashes = [hashlib.sha256(piece).hexdigest() for piece in pieces]
            file_name = file_path.split("/")[-1]

            self.file_pieces[file_name] = pieces
            self.file_metadata[file_name] = {
                "piece_size": piece_size,
                "total_size": len(content),
                "piece_hashes": piece_hashes,
            }

    def get_metadata(self, file_name):
        with self.lock:
            return self.file_metadata.get(file_name)

    def get_piece(self, piece_index, file_name):
        with self.lock:
            pieces = self.file_pieces.get(file_name)
            if pieces and 0 <= piece_index < len(pieces):
                return pieces[piece_index]
            return None

    def get_all_info(self):
        with self.lock:
            return {
                "metadata": self.file_metadata.copy(),
                "pieces": {
                    file_name: [piece.hex() for piece in pieces]
                    for file_name, pieces in self.file_pieces.items()
                },
            }
