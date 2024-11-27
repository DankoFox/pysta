import threading
import hashlib
import pytest
from node.upload_manager import UploadManager, FileManager
from node.download_manager import DownloadManager


@pytest.fixture
def setup_upload_manager():
    """
    Pytest fixture to set up and run the UploadManager in a separate thread.
    Yields the UploadManager, original file name, and piece size.
    """
    file_manager = FileManager()

    # Prepare test file
    original_file = "file1.txt"
    piece_size = 2048
    file_manager.split_file(original_file, piece_size)

    # Start UploadManager server
    upload_manager = UploadManager("127.0.0.1", 5000, file_manager)
    thread = threading.Thread(target=upload_manager.start_server, daemon=True)
    thread.start()

    yield upload_manager, original_file, piece_size

    # Teardown after test
    upload_manager.stop_server()


def test_download_manager(setup_upload_manager):
    """
    Test the DownloadManager by downloading a file from the UploadManager.
    """
    # Extract setup data
    upload_manager, original_file, piece_size = setup_upload_manager

    # Get metadata from UploadManager
    file_manager = upload_manager.file_manager
    metadata = file_manager.get_metadata(original_file)

    assert metadata is not None, "Failed to fetch metadata from UploadManager."

    piece_hashes = metadata["piece_hashes"]
    total_size = metadata["total_size"]

    # Set up the DownloadManager
    downloaded_file = "downloaded_file1.txt"
    download_manager = DownloadManager(
        file_path=downloaded_file,
        piece_size=piece_size,
        piece_hashes=piece_hashes,
        file_size=total_size,
    )

    # Start downloading
    peer_address = ("127.0.0.1", 5000)
    download_manager.start_download(peer_address, original_file)

    # Verify file integrity
    with open(original_file, "rb") as f_original, open(
        downloaded_file, "rb"
    ) as f_downloaded:
        original_hash = hashlib.sha256(f_original.read()).hexdigest()
        downloaded_hash = hashlib.sha256(f_downloaded.read()).hexdigest()

    assert (
        original_hash == downloaded_hash
    ), "Downloaded file does not match the original."


def test_small_file_download(setup_upload_manager):
    upload_manager, _, piece_size = setup_upload_manager

    # Create a small file and split it
    small_file = "small_file.txt"
    with open(small_file, "wb") as f:
        f.write(b"Small file content.")
    upload_manager.file_manager.split_file(small_file, piece_size)

    print("\n============================================================\n")
    print(
        f"Metadata after splitting {small_file}: {upload_manager.file_manager.get_metadata(small_file)}"
    )

    metadata = upload_manager.file_manager.get_metadata(small_file)
    assert metadata is not None, "Failed to fetch metadata for small file."
    print(upload_manager.file_manager.get_all_info())

    print("\n++++++++++++++++++++START DOWNLOADING++++++++++++++++\n")

    # Test download for small file
    piece_hashes = metadata["piece_hashes"]
    total_size = metadata["total_size"]
    downloaded_file = "downloaded_small_file.txt"
    download_manager = DownloadManager(
        file_path=downloaded_file,
        piece_size=piece_size,
        piece_hashes=piece_hashes,
        file_size=total_size,
    )
    peer_address = ("127.0.0.1", 5000)
    download_manager.start_download(peer_address, small_file)

    # Verify
    with open(small_file, "rb") as f_original, open(
        downloaded_file, "rb"
    ) as f_downloaded:
        original_content = f_original.read()
        downloaded_content = f_downloaded.read()

        print(f"Original file content: {original_content}")
        print(f"Downloaded file content: {downloaded_content}")

        original_hash = hashlib.sha256(original_content).hexdigest()
        downloaded_hash = hashlib.sha256(downloaded_content).hexdigest()

        print(f"Original file hash: {original_hash}")
        print(f"Downloaded file hash: {downloaded_hash}")

        assert (
            original_hash == downloaded_hash
        ), "Downloaded small file does not match original."


def test_large_file_download(setup_upload_manager):
    upload_manager, _, piece_size = setup_upload_manager

    # Create a large file and split it
    large_file = "large_file.txt"
    large_content = b"A" * (10 * 2048 * 1000)  # 10 pieces
    with open(large_file, "wb") as f:
        f.write(large_content)

    upload_manager.file_manager.split_file(large_file, piece_size)
    metadata = upload_manager.file_manager.get_metadata(large_file)
    assert metadata is not None, "Failed to fetch metadata for large file."

    # print(f"Metadata for large file: {metadata}")

    # Test download for large file
    piece_hashes = metadata["piece_hashes"]
    total_size = metadata["total_size"]
    downloaded_file = "downloaded_large_file.txt"
    download_manager = DownloadManager(
        file_path=downloaded_file,
        piece_size=piece_size,
        piece_hashes=piece_hashes,
        file_size=total_size,
    )
    peer_address = ("127.0.0.1", 5000)
    download_manager.start_download(peer_address, large_file)

    # Verify
    with open(large_file, "rb") as f_original, open(
        downloaded_file, "rb"
    ) as f_downloaded:
        original_content = f_original.read()
        downloaded_content = f_downloaded.read()

        assert (
            original_content == downloaded_content
        ), "Downloaded large file does not match original."


def test_corrupted_piece_detection(setup_upload_manager):
    upload_manager, _, piece_size = setup_upload_manager

    # Create a test file and split it
    test_file = "test_file.txt"
    with open(test_file, "wb") as f:
        f.write(b"Test file content for corruption test.")
    upload_manager.file_manager.split_file(test_file, piece_size)

    metadata = upload_manager.file_manager.get_metadata(test_file)
    assert metadata is not None, "Failed to fetch metadata for test file."

    # Simulate corrupted piece
    piece_hashes = metadata["piece_hashes"]
    total_size = metadata["total_size"]
    downloaded_file = "corrupted_downloaded_file.txt"

    class CorruptedDownloadManager(DownloadManager):
        def receive_piece(self, sock, piece_index):
            # Simulate receiving corrupted data
            piece_data = super().receive_piece(sock, piece_index)
            if piece_index == 0:  # Corrupt the first piece
                return b"CORRUPTED DATA"
            return piece_data

    download_manager = CorruptedDownloadManager(
        file_path=downloaded_file,
        piece_size=piece_size,
        piece_hashes=piece_hashes,
        file_size=total_size,
    )
    peer_address = ("127.0.0.1", 5000)

    try:
        download_manager.start_download(peer_address, test_file)
        assert False, "Corrupted piece was not detected!"
    except AssertionError as e:
        print(f"Expected error occurred: {e}")


def test_missing_metadata(setup_upload_manager):
    upload_manager, _, _ = setup_upload_manager

    # Request metadata for a non-existent file
    non_existent_file = "non_existent_file.txt"
    metadata = upload_manager.file_manager.get_metadata(non_existent_file)
    print(f"METADATA_MISSING: {metadata}")
    assert metadata is None, "Metadata for non-existent file should be None."

    # Simulate requesting metadata over the network
    peer_address = ("127.0.0.1", 5000)
    download_manager = DownloadManager(
        file_path="non_existent_downloaded.txt",
        piece_size=2048,
        piece_hashes=[],
        file_size=0,
    )
    download_manager.start_download(peer_address, non_existent_file)


# def test_concurrent_downloads(setup_upload_manager):
#     upload_manager, original_file, piece_size = setup_upload_manager
#
#     # Prepare metadata for concurrent downloads
#     metadata = upload_manager.file_manager.get_metadata(original_file)
#     piece_hashes = metadata["piece_hashes"]
#     total_size = metadata["total_size"]
#
#     # Start multiple downloads concurrently
#     def download_task(file_suffix):
#         downloaded_file = f"downloaded_{file_suffix}.txt"
#         download_manager = DownloadManager(
#             file_path=downloaded_file,
#             piece_size=piece_size,
#             piece_hashes=piece_hashes,
#             file_size=total_size,
#         )
#         peer_address = ("127.0.0.1", 5000)
#         download_manager.start_download(peer_address, original_file)
#
#         # Verify integrity
#         with open(original_file, "rb") as f_original, open(
#             downloaded_file, "rb"
#         ) as f_downloaded:
#             assert f_original.read() == f_downloaded.read(), f"{file_suffix} mismatch"
#
#     threads = [threading.Thread(target=download_task, args=(i,)) for i in range(5)]
#     for t in threads:
#         t.start()
#     for t in threads:
#         t.join()
#
#     print("Concurrent downloads completed successfully.")


def test_image_file_download(setup_upload_manager):
    upload_manager, _, piece_size = setup_upload_manager

    # Create a small file and split it
    readme = "TESTING_IMAGE.png"
    upload_manager.file_manager.split_file(readme, piece_size)

    print("\n============================================================\n")
    print(
        f"Metadata after splitting {readme}: {upload_manager.file_manager.get_metadata(readme)}"
    )

    metadata = upload_manager.file_manager.get_metadata(readme)
    assert metadata is not None, "Failed to fetch metadata for small file."
    print(upload_manager.file_manager.get_all_info())

    print("\n++++++++++++++++++++START DOWNLOADING++++++++++++++++\n")

    # Test download for small file
    piece_hashes = metadata["piece_hashes"]
    total_size = metadata["total_size"]
    downloaded_file = "downloaded_image_file.png"
    download_manager = DownloadManager(
        file_path=downloaded_file,
        piece_size=piece_size,
        piece_hashes=piece_hashes,
        file_size=total_size,
    )
    peer_address = ("127.0.0.1", 5000)
    download_manager.start_download(peer_address, readme)

    # Verify
    with open(readme, "rb") as f_original, open(downloaded_file, "rb") as f_downloaded:
        original_content = f_original.read()
        downloaded_content = f_downloaded.read()

        print(f"Original file content: {original_content}")
        print(f"Downloaded file content: {downloaded_content}")

        original_hash = hashlib.sha256(original_content).hexdigest()
        downloaded_hash = hashlib.sha256(downloaded_content).hexdigest()

        print(f"Original file hash: {original_hash}")
        print(f"Downloaded file hash: {downloaded_hash}")

        assert (
            original_hash == downloaded_hash
        ), "Downloaded small file does not match original."
