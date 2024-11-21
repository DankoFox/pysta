# UploadManager vs. DownloadManager in P2P Networks

The **UploadManager** and **DownloadManager** serve complementary but distinct roles in a peer-to-peer (P2P) network. Here’s a breakdown of their key differences:

## 1. Purpose

### UploadManager
- Acts as the server-side component of a node.
- Handles incoming requests from peers for specific file pieces.
- Sends the requested file pieces to peers.

### DownloadManager
- Acts as the client-side component of a node.
- Initiates requests to other peers for specific file pieces.
- Receives and processes the requested pieces to assemble the file.

## 2. Responsibilities

### UploadManager
- Listens for incoming peer connections.
- Processes requests (e.g., "GET_PIECE") for specific file pieces.
- Verifies that requested pieces exist and retrieves them via the FileManager.
- Sends the pieces to the requesting peer.

### DownloadManager
- Selects which peers to request pieces from (may involve strategies like "rarest first").
- Sends requests to peers for specific pieces.
- Validates received pieces (e.g., by checking hashes).
- Passes valid pieces to the FileManager for storage.

## 3. Communication Direction

### UploadManager
- Waits for and responds to requests from other peers (passive role).

### DownloadManager
- Actively initiates connections and sends requests to other peers (active role).

## 4. Dependencies

### UploadManager
- Relies on the FileManager to fetch the data for the requested pieces.
- Needs a file to be available locally to serve as a source.

### DownloadManager
- Relies on the FileManager to store received pieces and validate them.
- Needs a list of peers (or a tracker) to know where to request pieces.

## 5. Error Handling

### UploadManager
- Handles errors like invalid requests (e.g., malformed "GET_PIECE") or requests for unavailable pieces.
- Typically sends error messages back to the requester.

### DownloadManager
- Handles errors like connection failures, timeouts, or receiving corrupt pieces.
- Re-attempts downloads from other peers if needed.

## 6. Peer-to-Peer Interaction

### UploadManager
- Makes the node useful to the network by sharing pieces with others.

### DownloadManager
- Makes the node consume resources from the network by downloading pieces.
