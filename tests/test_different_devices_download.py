import os
import socket
import threading
import hashlib
from node.upload_manager import UploadManager
from node.download_manager import DownloadManager
from node.file_manager import FileManager


def create_test_file(file_path, content):
    """Utility function to create a test file with given content."""
    with open(file_path, "wb") as f:
        f.write(content)


def calculate_file_hash(file_path):
    """Utility function to calculate the SHA-256 hash of a file."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_download_from_another_device():
    """Test downloading a file from another device."""
    # Setup for Device A (Uploader)
    uploader_host = "127.0.0.1"
    uploader_port = 5000
    file_manager_a = FileManager()
    upload_manager = UploadManager(uploader_host, uploader_port, file_manager_a)

    # Create and split the test file
    test_file_path = "test_file.txt"
    test_content = b"Hello, this is a test file for cross-device download."
    create_test_file(test_file_path, test_content)
    piece_size = 16  # Split into 16-byte pieces
    file_manager_a.split_file(test_file_path, piece_size)

    # Start UploadManager in a separate thread
    threading.Thread(target=upload_manager.start_server, daemon=True).start()

    # Setup for Device B (Downloader)
    downloader_host = "127.0.0.1"
    downloader_port = 5001
    save_path = "downloaded_test_file.txt"

    # Retrieve metadata from Device A
    file_name = os.path.basename(test_file_path)
    metadata = file_manager_a.get_metadata(file_name)
    assert metadata is not None, "Metadata retrieval failed on Device A."

    # Initialize DownloadManager on Device B
    download_manager = DownloadManager(
        file_path=save_path,
        piece_size=piece_size,
        piece_hashes=metadata["piece_hashes"],
        file_size=metadata["total_size"],
    )

    # Simulate peer-to-peer download
    peer_address = (uploader_host, uploader_port)
    download_manager.start_download(peer_address, file_name)

    # Validate the downloaded file matches the original
    original_hash = calculate_file_hash(test_file_path)
    downloaded_hash = calculate_file_hash(save_path)
    assert original_hash == downloaded_hash, "Downloaded file hash mismatch."

    # Cleanup
    upload_manager.stop_server()
    os.remove(test_file_path)
    os.remove(save_path)
