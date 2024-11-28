from node.upload_manager import UploadManager
from node.file_manager import FileManager
import threading
import socket


def get_real_ip():
    """
    Get the real (public-facing) IP address of the host.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Google's public DNS server
            return s.getsockname()[0]
    except Exception as e:
        print(f"Error determining real IP: {e}")
        return "Unknown"


def get_local_ip():
    """
    Get the local network IP address of the host.
    """
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception as e:
        print(f"Error determining local IP: {e}")
        return "Unknown"


# Set up the UploadManager
HOST = "0.0.0.0"  # Allow connections from other devices
PORT = 5000
PIECE_SIZE = 16  # Adjust as needed

file_manager = FileManager()
upload_manager = UploadManager(HOST, PORT, file_manager)

# Prepare the file for upload
TEST_FILE = "test_REAL_file.txt"
with open(TEST_FILE, "wb") as f:
    f.write(
        b"Hello, this is a test file for cross-device download. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam molestie ut ligula sit amet porta. Suspendisse luctus augue at odio mattis porttitor. Nulla facilisis purus convallis lectus ullamcorper sollicitudin. Duis consequat lobortis elementum. Curabitur feugiat a turpis eget egestas. Cras varius velit id hendrerit placerat. Fusce eu efficitur ante. Etiam porttitor nibh vel eros egestas tempus. Aenean luctus molestie augue. "
    )
file_manager.split_file(TEST_FILE, PIECE_SIZE)


# Run the server
def start_server():
    upload_manager.start_server()


if __name__ == "__main__":
    # Get the real and local IP addresses
    real_ip = get_real_ip()
    local_ip = get_local_ip()

    print(f"Starting UploadServer on {HOST}:{PORT}")
    print(f"Local IP: {local_ip}:{PORT}")
    print(f"Real/Public IP: {real_ip}:{PORT} (if accessible)")

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    input("Press Enter to stop the server...\n")
    upload_manager.stop_server()
