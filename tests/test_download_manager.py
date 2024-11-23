import pytest
import time
import tempfile
import os
import hashlib
from node.download_manager import DownloadManager
from tests.mock_upload_server import MockUploadServer


@pytest.fixture
def setup_mock_server():
    # Mock file content and configuration
    file_content = b"The more I look into it, the more it stains onto my broken mind. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur vel molestie sapien. Nam vitae ornare diam, vitae imperdiet ipsum. Praesent dictum ex eu massa sodales tristique. Nulla eget neque id sem consectetur mattis ut a ex. Nam et rutrum magna. Integer id maximus libero. Maecenas accumsan id leo fermentum interdum. Suspendisse potenti. Cras eget aliquet dui, nec efficitur est. In vehicula massa quis purus pellentesque, sed tristique lacus bibendum. Quisque vitae magna et sem suscipit hendrerit."
    piece_size = 20
    file_size = len(file_content)

    piece_hashes = [
        hashlib.sha256(
            file_content[
                i : (
                    i + piece_size
                    if i + piece_size <= len(file_content)
                    else len(file_content)
                )
            ]
        ).hexdigest()
        for i in range(0, len(file_content), piece_size)
    ]

    # Start mock server
    host = "127.0.0.1"
    server = MockUploadServer(host, 0, file_content, piece_size)
    server.start()
    port = server.server_socket.getsockname()[1]

    yield host, port, file_content, piece_size, file_size, piece_hashes

    # Stop the server
    server.stop()
    print("\n=================================================\n")
    time.sleep(2)


def test_piece_hashes():
    file_content = b"The more I look into it, the more it stains onto my broken mind. "
    piece_size = 10

    # Correct hash calculation
    expected_piece_hashes = []
    for i in range(0, len(file_content), piece_size):
        end = min(i + piece_size, len(file_content))
        expected_piece_hashes.append(hashlib.sha256(file_content[i:end]).hexdigest())

    # Generate hashes using the corrected logic
    piece_hashes = [
        hashlib.sha256(
            file_content[
                i : (
                    i + piece_size
                    if i + piece_size <= len(file_content)
                    else len(file_content)
                )
            ]
        ).hexdigest()
        for i in range(0, len(file_content), piece_size)
    ]

    assert piece_hashes == expected_piece_hashes, "Piece hashes calculation failed!"


def test_download_manager(setup_mock_server):
    host, port, file_content, piece_size, file_size, piece_hashes = setup_mock_server
    print(f"WHAT DA HELLLLLLLLLLLLLLLLLLL, PIECE SIZE = {piece_size}")

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    try:
        download_manager = DownloadManager(
            file_path, piece_size, piece_hashes, file_size
        )
        download_manager.start_download((host, port))

        for i in range(len(piece_hashes)):
            start = i * piece_size
            end = min(start + piece_size, len(file_content))
            expected_piece = file_content[start:end]

            print(f"Expected piece {i}: {expected_piece}")

            with open(file_path, "rb") as f:
                f.seek(start)
                downloaded_piece = f.read(len(expected_piece))

            print(f"Downloaded piece {i}: {downloaded_piece}")

            assert (
                downloaded_piece == expected_piece
            ), f"Mismatch in piece {i}. Expected: {expected_piece}, Got: {downloaded_piece}"

        with open(file_path, "rb") as f:
            downloaded_content = f.read()
        print(f"Full downloaded content: {downloaded_content}")

        assert (
            downloaded_content == file_content
        ), "Downloaded file content does not match original content."

    finally:
        os.remove(file_path)


def test_invalid_piece_hash(setup_mock_server):
    host, port, file_content, piece_size, file_size, piece_hashes = setup_mock_server

    # Modify the hash for the first piece to be invalid
    invalid_piece_hashes = [piece_hashes[0] + "invalid"] + piece_hashes[1:]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    try:
        # Initialize and start DownloadManager with the invalid piece hashes
        download_manager = DownloadManager(
            file_path, piece_size, invalid_piece_hashes, file_size
        )
        download_manager.start_download((host, port))

        # Verify that the first piece failed verification and was not written to the file
        with open(file_path, "rb") as f:
            f.seek(0)
            downloaded_piece = f.read(piece_size)

            assert (
                downloaded_piece != file_content[:piece_size]
            ), "Invalid piece was written to the file."
    finally:
        os.remove(file_path)


def test_all_pieces_invalid(setup_mock_server):
    host, port, file_content, piece_size, file_size, piece_hashes = setup_mock_server

    # Modify all the hashes to be incorrect
    invalid_piece_hashes = [piece_hash + "invalid" for piece_hash in piece_hashes]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    try:
        # Initialize and start DownloadManager with invalid hashes
        download_manager = DownloadManager(
            file_path, piece_size, invalid_piece_hashes, file_size
        )
        download_manager.start_download((host, port))

        # Check that no pieces were written to the file
        with open(file_path, "rb") as f:
            downloaded_content = f.read()
        print(
            f"Downloaded content (should be empty or incorrect): {downloaded_content}"
        )

        # Verify the file is empty or contains invalid data
        assert (
            downloaded_content != file_content
        ), "Downloaded content should not match the original content."

    finally:
        os.remove(file_path)


def test_partial_piece_success(setup_mock_server):
    host, port, file_content, piece_size, file_size, piece_hashes = setup_mock_server

    # Modify the hash for the first piece to be invalid
    invalid_piece_hashes = [piece_hashes[0] + "invalid"] + piece_hashes[1:]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    try:
        # Initialize and start DownloadManager with partially invalid hashes
        download_manager = DownloadManager(
            file_path, piece_size, invalid_piece_hashes, file_size
        )
        download_manager.start_download((host, port))

        # Print the downloaded content
        with open(file_path, "rb") as f:
            downloaded_content = f.read()
        print(f"Downloaded content (partial success): {downloaded_content}")

        # Verify that only the valid pieces are written
        # The first piece should be empty (or filled with '\x00')
        expected_content = (
            b"\x00" * piece_size + file_content[piece_size:]
        )  # First piece is empty

        assert (
            downloaded_content == expected_content
        ), f"Downloaded content doesn't match expected (partial success). Expected: {expected_content}, Got: {downloaded_content}"

    finally:
        os.remove(file_path)


def test_partial_piece_middle_failure(setup_mock_server):
    host, port, file_content, piece_size, file_size, piece_hashes = setup_mock_server

    # Simulate corruption in a middle piece (e.g., second piece)
    corrupted_piece_hashes = piece_hashes[:]
    corrupted_piece_hashes[1] = (
        corrupted_piece_hashes[1] + "invalid"
    )  # Corrupt the second piece's hash

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    try:
        # Initialize and start DownloadManager with the corrupted hash in the middle
        download_manager = DownloadManager(
            file_path, piece_size, corrupted_piece_hashes, file_size
        )
        download_manager.start_download((host, port))

        # Print the downloaded content
        with open(file_path, "rb") as f:
            downloaded_content = f.read()
        print(f"Downloaded content (partial middle failure): {downloaded_content}")

        # Expected content:
        # - First valid piece is the same as the original
        # - Corrupted piece should be filled with '\x00'
        # - Valid pieces after the corrupted one should match the original content
        expected_content = (
            file_content[:piece_size]  # First piece is valid
            + b"\x00" * piece_size  # Corrupted second piece is empty
            + file_content[
                piece_size * 2 :
            ]  # Remaining valid pieces after the corrupted one
        )

        # Assert that the downloaded content matches the expected content
        assert (
            downloaded_content == expected_content
        ), f"Downloaded content doesn't match expected (middle failure). Expected: {expected_content}, Got: {downloaded_content}"

    finally:
        os.remove(file_path)


def test_large_file_download(setup_mock_server):
    host, port, file_content, piece_size, file_size, piece_hashes = setup_mock_server

    # Simulate a larger file by repeating the content multiple times
    large_file_content = file_content * 8
    large_piece_hashes = [
        hashlib.sha256(large_file_content[i : i + piece_size]).hexdigest()
        for i in range(0, len(large_file_content), piece_size)
    ]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    try:
        # Initialize and start DownloadManager with the larger file
        download_manager = DownloadManager(
            file_path, piece_size, large_piece_hashes, len(large_file_content)
        )
        download_manager.start_download((host, port))

        # Print the downloaded content
        with open(file_path, "rb") as f:
            downloaded_content = f.read()
        print(
            f"Downloaded content for large file (first 100 bytes): {downloaded_content[:100]}"
        )

        # Verify the downloaded content matches the large file content
        assert (
            downloaded_content == large_file_content
        ), "Downloaded large file content doesn't match."

    finally:
        os.remove(file_path)


def test_large_number_of_small_pieces(setup_mock_server):
    host, port, file_content, piece_size, file_size, piece_hashes = setup_mock_server

    # Simulate a file with many small pieces (e.g., 1 byte per piece)
    small_piece_size = 1
    small_piece_hashes = [
        hashlib.sha256(file_content[i : i + small_piece_size]).hexdigest()
        for i in range(0, len(file_content), small_piece_size)
    ]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    try:
        # Initialize and start DownloadManager with many small pieces
        download_manager = DownloadManager(
            file_path, small_piece_size, small_piece_hashes, len(file_content)
        )
        download_manager.start_download((host, port))

        # Print downloaded content
        with open(file_path, "rb") as f:
            downloaded_content = f.read()
        print(
            f"Downloaded content for large number of small pieces (first 100 bytes): {downloaded_content[:100]}"
        )

        # Verify the downloaded content matches the original file content
        assert (
            downloaded_content == file_content
        ), "Downloaded file content with many small pieces doesn't match."

    finally:
        os.remove(file_path)
