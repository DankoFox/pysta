import hashlib
from node.file_manager import FileManager
from node.upload_manager import UploadManager

file_manager = FileManager()

# Split files with different piece sizes
file_manager.split_file("file1.txt", piece_size=20)
file_manager.split_file("file2.txt", piece_size=512)

# Access metadata for each file
metadata_file1 = file_manager.get_metadata("file1.txt")
metadata_file2 = file_manager.get_metadata("file2.txt")

print("Metadata for file1.txt:", metadata_file1)
print("Metadata for file2.txt:", metadata_file2)

# Retrieve a specific piece
piece = file_manager.get_piece(0, "file1.txt")
print("First piece of file1.txt:", piece)

# Verify piece hashes
assert (
    metadata_file1["piece_hashes"][0] == hashlib.sha256(piece).hexdigest()
), "Hash mismatch for file1.txt piece 0"
print("Hash verification passed for file1.txt piece 0")
