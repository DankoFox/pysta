import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import socket
import json
import hashlib
from node.download_manager import DownloadManager


def calculate_file_hash(file_path):
    """Utility function to calculate the SHA-256 hash of a file."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def fetch_metadata(host, port, file_name):
    """Fetch file metadata (e.g., piece hashes) from the server."""
    try:
        with socket.create_connection((host, port)) as sock:
            sock.sendall(f"GET_METADATA {file_name}\n".encode())
            response = sock.recv(4096).decode()
            metadata = json.loads(response)
            if "piece_hashes" in metadata and "total_size" in metadata:
                return metadata
            else:
                raise ValueError("Invalid metadata format.")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch metadata: {e}")


# Configure the downloader
HOST = "DEVICE_A_IP"  # Replace with Device A's IP address
PORT = 5000
FILE_NAME = "test_REAL_file.txt"
SAVE_PATH = "downloaded_REAL_test_file.txt"

try:
    # Fetch metadata from the UploadManager
    metadata = fetch_metadata(HOST, PORT, FILE_NAME)
    PIECE_SIZE = metadata["piece_size"]
    PIECE_HASHES = metadata["piece_hashes"]
    FILE_SIZE = metadata["total_size"]

    print(f"Metadata fetched successfully for {FILE_NAME}: {metadata}")

    # Initialize the DownloadManager
    download_manager = DownloadManager(
        file_path=SAVE_PATH,
        piece_size=PIECE_SIZE,
        piece_hashes=PIECE_HASHES,
        file_size=FILE_SIZE,
    )

    # Start download
    print(f"Connecting to {HOST}:{PORT} to download {FILE_NAME}")
    peer_address = (HOST, PORT)
    download_manager.start_download(peer_address, FILE_NAME)

    # Verify the downloaded file
    original_hash = calculate_file_hash(FILE_NAME)  # Recalculate from the original file
    downloaded_hash = calculate_file_hash(SAVE_PATH)
    assert original_hash == downloaded_hash, "File integrity check failed!"

    print(f"File {FILE_NAME} downloaded successfully and verified.")
except Exception as e:
    print(f"Download failed: {e}")
