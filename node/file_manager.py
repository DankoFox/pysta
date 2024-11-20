import os
import hashlib


class FileManager:
    def __init__(self, piece_size, piece_hashes: dict):
        """
        Initialize the FileManager.
        :param piece_size: Size of each piece in bytes (default 512KB).
        """
        self.piece_size = piece_size
        self.piece_hashes = piece_hashes

    def split_file(self, file_path):
        """
        Splits a file into pieces and calculates their hashes.
        :param file_path: Path to the file to split.
        :return: A dictionary mapping piece index to its hash.
        """
        not_a_file = not os.path.isfile(file_path)
        if not_a_file:
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as file:
            index = 0
            while True:
                piece = file.read(self.piece_size)
                if not piece:
                    break
                piece_hash = hashlib.sha1(piece).hexdigest()
                self.piece_hashes[index] = piece_hash
                index += 1

            if not self.piece_hashes:
                print("Warning: File is empty, no pieces to split.")

        return self.piece_hashes

    def merge_pieces(self, pieces, output_path):
        """
        Merges pieces into a single file.
        :param pieces: A dictionary where keys are piece indices and values are piece data.
        :param output_path: Path to save the merged file.
        """
        with open(output_path, "wb") as file:
            for index in sorted(pieces.keys()):
                file.write(pieces[index])

    def get_total_pieces(self, file_path):
        """
        Calculate the total number of pieces for a file.
        :param file_path: Path to the file.
        :return: Total number of pieces.
        """
        not_a_file = not os.path.isfile(file_path)

        if not_a_file:
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        return (file_size + self.piece_size - 1) // self.piece_size

    def get_piece(self, piece_index, file_path):
        """
        Retrieve a specific piece of the file.
        :param piece_index: Index of the piece to retrieve.
        :param file_path: Path to the file.
        :return: Byte data of the requested piece or None if invalid index.
        """
        try:
            not_a_file = not os.path.isfile(file_path)
            if not_a_file:
                raise FileNotFoundError(f"File not found: {file_path}")

            # Calculate the starting position of the piece
            start = piece_index * self.piece_size
            end = start + self.piece_size

            # Get file size to check bounds
            file_size = os.path.getsize(file_path)
            if start >= file_size:  # Index out of range
                return None

            # Adjust end for the last piece
            if end > file_size:
                end = file_size

            # Read and return the piece
            with open(file_path, "rb") as file:
                file.seek(start)
                return file.read(end - start)

        except Exception as e:
            print(f"Error retrieving piece {piece_index}: {e}")
            return None

    @staticmethod
    def hash_piece(piece_data):
        """
        Calculate the SHA1 hash of a piece.
        :param piece_data: Byte data of the piece.
        :return: Hexadecimal SHA1 hash.
        """
        return hashlib.sha1(piece_data).hexdigest()
