import threading
import requests
import socket
import time
import signal
import json

import sys
import os

# Add the project root to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from node.upload_manager import UploadManager
from node.download_manager import (
    DownloadManager,
)  # Placeholder for your DownloadManager

from node.file_manager import FileManager  # Your FileManager implementation


TRACKER_URL = "http://127.0.0.1:6969"


class PeerClient:
    def __init__(self, peer_id, ip, port, shared_files, tracker_url):
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
        self.tracker_url = tracker_url
        self.file_manager = FileManager()  # Manages file metadata and pieces
        self.upload_manager = UploadManager(ip, port, self.file_manager)
        self.running = True

    def start_upload_manager(self):
        """
        Start the UploadManager in a separate thread.
        """
        threading.Thread(target=self.upload_manager.start_server, daemon=True).start()
        print(f"UploadManager running on {self.ip}:{self.port}")

    def handle_commands(self):
        """
        Command-line interface for the peer client.
        """
        print("Enter 'query <file_name>' to search for a file.")
        print("Enter 'upload <file_path>' to share a new file.")
        print("Enter 'exit' to stop the peer client.")

        while self.running:
            command = input(">> ").strip()
            if command.startswith("query "):
                file_name = command.split(" ", 1)[1]
                self.query_file(file_name)

            elif command.startswith("download"):
                parts = command.split(" ", 2)
                if len(parts) == 3:
                    file_name, save_path = parts[1:]
                    self.query_and_download(file_name, save_path)
                else:
                    print("Usage: download <file_name> <save_path>")

            elif command == "tracker_status":
                self.query_tracker_status()

            elif command.startswith("upload "):
                file_path = command.split(" ", 1)[1]
                self.upload_file(file_path)

            elif command == "exit":
                print("Stopping peer client...")
                self.running = False
            else:
                print("Unknown command. Try 'query <file_name>' or 'exit'.")

    def query_tracker_status(self):
        """
        Query the tracker for its current status, including detailed file sharing information.
        """
        try:
            response = requests.get(f"{self.tracker_url}/status")  # Assuming self.tracker_url is the tracker's base URL
            if response.status_code == 200:
                data = response.json()
                print("Tracker Status:")
                print(f"  Tracker ID: {data.get('tracker_id', 'Unknown')}")
                print(f"  Peers Count: {data.get('peers_count', 0)}")
                print(f"  Files Count: {data.get('files_count', 0)}")
                print("  Files Information:")

                files_info = data.get("files_info", {})
                if not files_info:
                    print("    No files being shared.")
                else:
                    for file_name, details in files_info.items():
                        print(f"    - File Name: {file_name}")
                        print(f"      Peers Sharing ({details['peers_count']}):")
                        for peer in details["peers"]:
                            print(f"        Peer ID: {peer['peer_id']}, IP: {peer['ip']}, Port: {peer['port']}")
            else:
                print(f"Failed to fetch tracker status. Error: {response.text}")
        except Exception as e:
            print(f"Error querying tracker status: {e}")


    def query_file(self, file_name):
        """
        Query the tracker for peers sharing a specific file.
        """
        try:
            response = requests.get(
                f"{self.tracker_url}/query", params={"file_name": file_name}
            )
            if response.status_code == 200:
                nodes = response.json()["nodes"]
                if nodes:
                    print(f"Peers sharing '{file_name}': {nodes}")
                else:
                    print(f"No peers found for file '{file_name}'.")
            else:
                print(
                    f"Query failed: {response.json().get('message', 'Unknown error')}"
                )
        except requests.RequestException as e:
            print(f"Error querying tracker: {e}")

    def register_with_tracker(self):
        """
        Register the peer and its files with the tracker.
        """
        file_metadata = []

        # Process files to calculate metadata and prepare for sharing
        for file_path in self.shared_files:
            piece_size = 512 * 1024  # 512 KB chunks
            self.file_manager.split_file(file_path, piece_size)

            # Get metadata to extract information
            file_name = file_path.split("/")[-1]
            metadata = self.file_manager.get_metadata(file_name)
            if metadata:
                file_metadata.append(
                    {
                        "file_name": file_name,
                        "piece_size": metadata["piece_size"],
                        "total_size": metadata["total_size"],
                        "piece_hashes": metadata["piece_hashes"],
                    }
                )

        # Send registration data to the tracker
        payload = {
            "peer_id": self.peer_id,
            "ip": self.ip,
            "port": self.port,
            "files": file_metadata,
        }

        try:
            response = requests.post(f"{self.tracker_url}/register", json=payload)
            if response.status_code == 200:
                print(f"Successfully registered with tracker: {response.json()}")
            else:
                print(f"Failed to register with tracker: {response.json()}")
        except requests.RequestException as e:
            print(f"Error registering with tracker: {e}")

    def upload_file(self, file_path):
        """
        Upload new file metadata to the tracker and share the file.
        :param file_path: Path of the file to upload.
        """
        try:
            # Split the file into pieces and get metadata
            piece_size = 512 * 1024  # 512 KB chunks
            self.file_manager.split_file(file_path, piece_size)

            # Get metadata for the file
            file_name = file_path.split("/")[-1]
            metadata = self.file_manager.get_metadata(file_name)
            if not metadata:
                print(f"Error: Could not generate metadata for file '{file_name}'.")
                return

            # Prepare payload for the tracker (minimal format)
            payload = {
                "peer_id": self.peer_id,
                "file_name": file_name
            }

            # Send the payload to the tracker
            response = requests.post(f"{self.tracker_url}/upload", json=payload)
            if response.status_code == 200:
                print(f"Successfully uploaded file '{file_name}' to tracker.")
                # Update local state
                self.shared_files.append(file_path)
            else:
                print(f"Failed to upload file: {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            print(f"Error uploading file: {e}")


    def deregister_from_tracker(self):
        """
        Deregister the peer from the tracker.
        """
        payload = {"peer_id": self.peer_id}

        try:
            response = requests.post(f"{self.tracker_url}/deregister", json=payload)
            if response.status_code == 200:
                print(f"Successfully deregistered from tracker: {response.json()}")
            else:
                print(f"Failed to deregister from tracker: {response.json()}")
        except requests.RequestException as e:
            print(f"Error deregistering from tracker: {e}")

    def query_and_download(self, file_name, save_path):
        """
        Query the tracker for peers sharing the specified file and download it.
        :param file_name: The name of the file to download.
        :param save_path: Path to save the downloaded file.
        """
        try:
            # Query the tracker for peers sharing the file
            response = requests.get(
                f"{self.tracker_url}/query", params={"file_name": file_name}
            )
            if response.status_code != 200:
                print(
                    f"File not found on tracker: {response.json().get('message', 'Unknown error')}"
                )
                return

            nodes = response.json().get("nodes", [])
            if not nodes:
                print(f"No peers available for file: {file_name}")
                return

            print(f"Found peers for file '{file_name}':")
            for idx, peer in enumerate(nodes):
                print(
                    f"  {idx + 1}. {peer['ip']}:{peer['port']} (Peer ID: {peer['peer_id']})"
                )

            # Select the first available peer for simplicity
            peer = nodes[0]
            peer_ip, peer_port = peer["ip"], peer["port"]

            # Fetch metadata from the selected peer
            metadata = self.fetch_metadata(peer_ip, peer_port, file_name)
            if not metadata:
                print(f"Metadata not found for file '{file_name}'")
                return

            # Initialize and start the download
            download_manager = DownloadManager(
                file_path=save_path,
                piece_size=metadata["piece_size"],
                piece_hashes=metadata["piece_hashes"],
                file_size=metadata["total_size"],
            )
            download_manager.start_download((peer_ip, peer_port), file_name)
            print(f"Download complete for file '{file_name}'. Saved to '{save_path}'.")
        except requests.RequestException as e:
            print(f"Error querying tracker: {e}")
        except Exception as e:
            print(f"Error downloading file: {e}")

    @staticmethod
    def fetch_metadata(host, port, file_name):
        """Fetch file metadata (e.g., piece hashes) from the peer."""
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
                # print(f"Raw response received: {response}")

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

    def start(self):
        """
        Start the peer client and handle graceful shutdown.
        """
        self.register_with_tracker()

        self.start_upload_manager()

        # Handle graceful shutdown on SIGINT/SIGTERM
        def handle_signal(signal_received, frame):
            print("\nSignal received, stopping peer client...")
            self.running = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Start CLI for user commands
        self.handle_commands()

        # Deregister when stopping
        self.deregister_from_tracker()


def get_local_ip():
    """
    Get the real IP address of the machine.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to an external address; doesn't actually send data
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    # Peer-specific configuration

    tracker_url = input("Enter the tracker server URL (e.g., http://127.0.0.1:6969): ").strip()
    if not tracker_url:
        print("Invalid tracker URL. Exiting...")
        exit(1)

    peer_id = "peer_1"
    ip = get_local_ip()
    port = 5001
    shared_files = ["test_REAL_file.txt", "book.pdf"]  # Files to share

    # Start the peer client
    client = PeerClient(peer_id, ip, port, shared_files, tracker_url)
    client.start()

    print(f"Peer started with IP: {client.ip} : {client.port}")
