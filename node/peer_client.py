import threading
import time
import requests
from upload_manager import UploadManager
from download_manager import DownloadManager  # Placeholder for your DownloadManager
from node.file_manager import FileManager  # Your FileManager implementation

TRACKER_URL = "http://127.0.0.1:5000"


class PeerClient:
    def __init__(self, peer_id, ip, port, shared_files):
        """
        Initialize the peer client with its ID, IP, port, and files to share.
        :param peer_id: Unique ID for the peer.
        :param ip: IP address of the peer.
        :param port: Port for the UploadManager.
        :param shared_files: List of files to share.
        """
        self.peer_id = peer_id
        self.ip = ip
        self.port = port
        self.shared_files = shared_files
        self.file_manager = FileManager()  # Manages file metadata and pieces
        self.upload_manager = UploadManager(ip, port, self.file_manager)

    def start_upload_manager(self):
        """
        Start the UploadManager in a separate thread.
        """
        threading.Thread(target=self.upload_manager.start_server, daemon=True).start()
        print(f"UploadManager running on {self.ip}:{self.port}")

    def register_with_tracker(self):
        """
        Register the peer and its files with the tracker.
        """
        file_hashes = []
        file_metadata = {}

        # Process files to calculate metadata and prepare for sharing
        for file_path in self.shared_files:
            file_hash = self.file_manager.calculate_file_hash(file_path)
            piece_size = 1024 * 1024  # 1MB chunks
            piece_count = self.file_manager.split_file(file_path, piece_size)

            file_hashes.append(file_hash)
            file_metadata[file_hash] = {
                "file_path": file_path,
                "piece_count": piece_count,
            }

        # Send registration data to the tracker
        payload = {
            "peer_id": self.peer_id,
            "ip": self.ip,
            "port": self.port,
            "files": file_hashes,
        }

        try:
            response = requests.post(f"{TRACKER_URL}/register", json=payload)
            if response.status_code == 200:
                print(f"Successfully registered with tracker: {response.json()}")
            else:
                print(f"Failed to register with tracker: {response.json()}")
        except requests.RequestException as e:
            print(f"Error registering with tracker: {e}")

    def query_and_download(self, file_hash, save_path):
        """
        Query the tracker for peers sharing the specified file hash and download it.
        :param file_hash: The hash of the file to download.
        :param save_path: Path to save the downloaded file.
        """
        # Query the tracker for file information
        try:
            response = requests.get(
                f"{TRACKER_URL}/query", params={"file_hash": file_hash}
            )
            if response.status_code != 200:
                print(
                    f"File not found on tracker: {response.json().get('message', 'Unknown error')}"
                )
                return

            nodes = response.json()["nodes"]
            if not nodes:
                print(f"No peers available for file hash: {file_hash}")
                return

            print(f"Found peers for file {file_hash}: {nodes}")
            peer = nodes[0]  # Select the first peer for simplicity
            peer_ip, peer_port = peer["ip"], peer["port"]

            # Metadata retrieval (optional if the tracker provides metadata)
            metadata = self.file_manager.get_metadata(
                file_hash
            )  # Fetch metadata locally or via peer
            if not metadata:
                print(f"Metadata not found for file {file_hash}")
                return

            # Initialize the DownloadManager to download the file
            download_manager = DownloadManager(
                file_path=save_path,
                piece_size=1024 * 1024,
                piece_hashes=metadata["piece_hashes"],
                file_size=metadata["file_size"],
            )
            download_manager.start_download((peer_ip, peer_port), file_hash)
            print(f"Download complete for file {file_hash}. Saved to {save_path}.")
        except requests.RequestException as e:
            print(f"Error querying tracker: {e}")

    def start(self):
        """
        Start the peer client by running the UploadManager and registering with the tracker.
        """
        self.start_upload_manager()
        self.register_with_tracker()
        print("Peer client is up and running.")


if __name__ == "__main__":
    # Peer-specific configuration
    peer_id = "peer_1"
    ip = "127.0.0.1"
    port = 5001
    shared_files = ["example1.txt", "example2.jpg"]  # Files to share

    # Start the peer client
    client = PeerClient(peer_id, ip, port, shared_files)
    client.start()

    # Simulate querying and downloading a file
    time.sleep(2)  # Wait for registration
    file_hash_to_download = "some_file_hash"  # Replace with actual file hash
    client.query_and_download(file_hash_to_download, "downloaded_example.txt")
