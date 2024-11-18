import os
from node.file_manager import FileManager
from node.downloader import Downloader


def test_downloader():
    file_manager = FileManager(piece_size=1024)  # 1KB for testing
    piece_hashes = {0: "fakehash0", 1: "fakehash1"}
    peers = [{"ip": "127.0.0.1", "port": 8080}, {"ip": "127.0.0.1", "port": 8081}]
    output_file = "downloaded_file.txt"

    # Simulate the downloader process (mocked for now)
    downloader = Downloader(file_manager, piece_hashes, peers, output_file)
    downloader.start_download()

    # Ensure output file is created (mock success for now)
    assert os.path.exists(output_file), "Downloaded file should exist."

    # Cleanup
    os.remove(output_file)


if __name__ == "__main__":
    test_downloader()
