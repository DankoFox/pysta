# **PySTA: Python Simple Torrent-like Application**

## **Overview**
PySTA is a Python-based implementation of a Simple Torrent-like Application (STA). It simulates the functionality of a peer-to-peer file-sharing network, incorporating a centralized tracker and multiple nodes capable of downloading and uploading files simultaneously. 

This project demonstrates:
- Multithreaded file transfer.
- Peer-to-peer communication using TCP/IP protocols.
- Centralized metadata management via a tracker.

---

## **Features**
- **Centralized Tracker**:
  - Manages metadata and tracks nodes' file availability.
  - Uses an HTTP-based protocol for communication.
- **Multidirectional Data Transfer (MDDT)**:
  - Simultaneously download multiple file pieces from different peers.
- **Peer-to-Peer File Sharing**:
  - Share files between nodes.
  - Start seeding downloaded files to other peers.
- **Metadata Management**:
  - Magnet text and `.torrent` file handling.
  - Accurate mapping between file pieces and their addresses.
- **Statistics Dashboard**:
  - Monitor upload/download progress in real-time.

---

## **Project Structure**
```plaintext
pysta/
├── tracker/                     # Tracker components
│   ├── tracker_server.py        # Tracker implementation
│   ├── metainfo_manager.py      # Handles .torrent metadata
│   └── peer_registry.py         # Manages peer and file data
├── node/                        # Node components
│   ├── node_client.py           # Node logic (download/upload)
│   ├── file_manager.py          # File and piece operations
│   ├── peer_communication.py    # Handles peer-to-peer protocols
│   └── upload_manager.py        # Upload logic for seeding
├── data/                        # Sample data and logs
│   ├── torrents/                # .torrent files
│   ├── logs/                    # Application logs
│   └── repository/              # Test files
├── tests/                       # Unit and integration tests
├── utils/                       # Helper utilities
│   ├── hashing.py               # File hashing utilities
│   ├── protocol_helpers.py      # Tracker and peer protocol utilities
│   └── network_utils.py         # Network helpers
├── main.py                      # Application entry point
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
└── setup.py                     # Project setup
```

## Requirements

- Python 3.9+
- Libraries:
  - Flask (for Tracker HTTP server)
  - asyncio (for asynchronous tasks)
  - Other dependencies in `requirements.txt`

## Installation

Clone the repository:

```sh
git clone https://github.com/DankoFox/pysta.git
cd pysta

