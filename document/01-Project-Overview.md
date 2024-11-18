# Objectives

- Use TCP/IP protocol stack for network communication.
- Support multi-direction data transfer (MDDT), enabling simultaneous downloads of multiple files from multiple peers.
- Implement tracker and node hosts to manage file-sharing functionality.
- Ensure multithreaded implementation for nodes to support concurrent uploads/downloads.

# Essential Components

## Tracker:
- A centralized server that tracks nodes and maintains metadata (file pieces availability).
- Handles communication with nodes via a minimal HTTP-based protocol.

## Node:
- A peer in the network with a local file repository.
- Shares metadata with the tracker and interacts with other nodes for file transfers.

# File Structure and Metadata

- **Magnet Text**: Points to a `.torrent` file containing metadata.
- **Metainfo File (.torrent)**:
  - Includes tracker address, piece length, piece count, file list, and mapping between pieces and files.
  - Must be accurately mapped for N pieces across M files.
- **Pieces**: Fixed-sized parts of a file (e.g., 512KB).
- **Files**: Comprised of multiple pieces.

# Protocols

## Tracker Protocol

### Requests:
- Nodes must announce themselves to the tracker at startup and provide a magnet text or metainfo file reference.
- Include start, stop, and completion states with download progress.

### Responses:
- Tracker replies with peer lists and optionally warning or error messages.
- Responses follow a dictionary structure:
  - `peers`: List of dictionaries with peer id, IP, and port.

## Peer-to-Peer Protocol

### Downloading:
- Nodes connect to listed peers and request missing pieces.
- Ensure MDDT is implemented: downloading multiple pieces from multiple peers simultaneously.
- Maintain a queue to track requested and received pieces.

### Uploading:
- Nodes share downloaded pieces with others.
- Implement tit-for-tat strategy to encourage cooperation.

# Advanced Features

## Tracker Enhancements:
- Support multiple trackers using DNS-based iterative or recursive queries.

## Peer Selection:
- Optimize block requests and avoid duplication.
- Handle disconnections gracefully.

# User Interface

## Basic requirements:
- Command-line or graphical interface to manage torrents.
- Show upload/download statistics.

## Advanced options:
- Implement features from Transmission CLI.

# Key Challenges

## Concurrency:
- Use multithreading to handle simultaneous file transfers and maintain responsiveness.

## Data Mapping:
- Map file pieces to the correct files accurately.

## Network Protocols:
- Implement robust client-server and peer-to-peer protocols.
