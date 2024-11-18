import os
import hashlib


class FileManager:
    def __init__(self, piece_size=512 * 1024):
        """
        Initialize the FileManager.
        :param piece_size: Size of each piece in bytes (default 512KB).
        """
        self.piece_size = piece_size

    def split_file(self, file_path):
        """
        Splits a file into pieces and calculates their hashes.
        :param file_path: Path to the file to split.
        :return: A dictionary mapping piece index to its hash.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        piece_hashes = {}
        with open(file_path, "rb") as f:
            index = 0
            while True:
                piece = f.read(self.piece_size)
                if not piece:
                    break
                piece_hash = hashlib.sha1(piece).hexdigest()
                piece_hashes[index] = piece_hash
                index += 1

        return piece_hashes

    def merge_pieces(self, pieces, output_path):
        """
        Merges pieces into a single file.
        :param pieces: A dictionary where keys are piece indices and values are piece data.
        :param output_path: Path to save the merged file.
        """
        with open(output_path, "wb") as f:
            for index in sorted(pieces.keys()):
                f.write(pieces[index])

    def get_total_pieces(self, file_path):
        """
        Calculate the total number of pieces for a file.
        :param file_path: Path to the file.
        :return: Total number of pieces.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        file_size = os.path.getsize(file_path)
        return (file_size + self.piece_size - 1) // self.piece_size

    @staticmethod
    def hash_piece(piece_data):
        """
        Calculate the SHA1 hash of a piece.
        :param piece_data: Byte data of the piece.
        :return: Hexadecimal SHA1 hash.
        """
        return hashlib.sha1(piece_data).hexdigest()
