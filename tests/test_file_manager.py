import os
from node.file_manager import FileManager


def test_file_manager():
    fm = FileManager(piece_size=1024)  # 1KB for testing
    test_file = "test_file.txt"
    output_file = "output_file.txt"

    # Create a test file
    with open(test_file, "w") as f:
        f.write("This is a test file for the FileManager module." * 100)

    # Test splitting the file
    piece_hashes = fm.split_file(test_file)
    assert len(piece_hashes) > 0, "File should be split into multiple pieces."

    # Create dummy pieces based on the split
    pieces = {}
    with open(test_file, "rb") as f:
        index = 0
        while True:
            piece = f.read(1024)
            if not piece:
                break
            pieces[index] = piece
            index += 1

    # Test merging the pieces
    fm.merge_pieces(pieces, output_file)
    assert os.path.exists(output_file), "Output file should be created."
    with open(test_file, "rb") as f1, open(output_file, "rb") as f2:
        assert f1.read() == f2.read(), "Merged file should match the original file."

    # Cleanup
    os.remove(test_file)
    os.remove(output_file)


if __name__ == "__main__":
    test_file_manager()
