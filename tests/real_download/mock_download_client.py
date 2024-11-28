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
            # Send a request for metadata
            sock.sendall(f"GET_METADATA {file_name}\n".encode())

            # Receive data until the delimiter is found
            response = ""
            while not response.endswith("\n\n"):
                chunk = sock.recv(4096).decode()  # Read up to 4096 bytes
                if not chunk:  # Connection closed unexpectedly
                    break
                response += chunk

            # Remove the delimiter
            response = response.strip()
            print(f"Raw response received: {response}")

            # Load the response as JSON
            metadata = json.loads(response)  # Parse the JSON string safely

            # Validate the metadata structure
            if (
                isinstance(metadata, dict)
                and "piece_size" in metadata
                and "total_size" in metadata
                and "piece_hashes" in metadata
            ):
                return metadata
            else:
                raise ValueError("Invalid metadata format.")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse metadata as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch metadata: {e}")


# Configure the downloader
HOST = "0.0.0.0"  # Replace with Device A's IP address
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
