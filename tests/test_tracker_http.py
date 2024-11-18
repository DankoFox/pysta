import requests

BASE_URL = "http://127.0.0.1:5000"

# Register a peer
response = requests.post(
    f"{BASE_URL}/register",
    json={
        "peer_id": "peer1",
        "ip": "192.168.1.2",
        "port": 6881,
        "files": ["filehash1", "filehash2"],
        "piece_count": 10,
        "magnet": "magnet:?xt=urn:btih:filehash1",
    },
)
print("Register Peer:", response.json())

# Query for peers with a specific file
response = requests.get(f"{BASE_URL}/query", params={"file_hash": "filehash1"})
print("Query File:", response.json())

# Update peer state
response = requests.post(
    f"{BASE_URL}/update",
    json={
        "peer_id": "peer1",
        "file_hash": "filehash1",
        "event": "started",
        "bytes_downloaded": 1024,
    },
)
print("Update Peer:", response.json())

# Check tracker status
response = requests.get(f"{BASE_URL}/status")
print("Tracker Status:", response.json())

# Test error cases
response = requests.get(f"{BASE_URL}/query", params={"file_hash": "nonexistenthash"})
print("Query Non-existent File:", response.json())

response = requests.post(
    f"{BASE_URL}/update",
    json={"peer_id": "unknown_peer", "file_hash": "unknown_file", "event": "started"},
)
print("Update Non-existent Peer/File:", response.json())
