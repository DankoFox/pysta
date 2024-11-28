from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# In-memory data structures
peers = {}  # {peer_id: {"ip": str, "port": int, "files": [file_hashes]}}
files = {}  # {file_hash: {"piece_count": int, "nodes": [peer_ids]}}
tracker_id = str(uuid.uuid4())  # Unique tracker ID


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    peer_id = data["peer_id"]
    ip = data["ip"]
    port = data["port"]
    files_list = data["files"]
    magnet = data.get("magnet")  # Optional

    # Update peer and file information 
    peers[peer_id] = {"ip": ip, "port": port, "files": files_list}
    for file_hash in files_list:
        if file_hash not in files:
            files[file_hash] = {"piece_count": data["piece_count"], "nodes": []}
        files[file_hash]["nodes"].append(peer_id)

    return (
        jsonify(
            {
                "status": "success",
                "message": f"Peer {peer_id} registered successfully.",
                "tracker_id": tracker_id,
            }
        ),
        200,
    )


@app.route("/query", methods=["GET"])
def query():
    file_hash = request.args.get("file_hash")
    if file_hash not in files:
        return jsonify({"status": "error", "message": "File not found."}), 404

    # Return detailed peer information
    node_details = [
        {"peer_id": peer_id, "ip": peers[peer_id]["ip"], "port": peers[peer_id]["port"]}
        for peer_id in files[file_hash]["nodes"]
    ]
    return jsonify({"status": "success", "nodes": node_details}), 200


@app.route("/update", methods=["POST"])
def update():
    data = request.json
    peer_id = data["peer_id"]
    file_hash = data["file_hash"]
    event = data["event"]  # started, stopped, or completed
    bytes_downloaded = data.get("bytes_downloaded", 0)

    if peer_id not in peers or file_hash not in files:
        return jsonify({"status": "error", "message": "Invalid peer or file."}), 400

    # Handle events
    if event == "started":
        if peer_id not in files[file_hash]["nodes"]:
            files[file_hash]["nodes"].append(peer_id)
    elif event == "stopped":
        files[file_hash]["nodes"].remove(peer_id)
    elif event == "completed":
        # Handle any specific logic for completed events if necessary
        pass

    return (
        jsonify(
            {
                "status": "success",
                "message": f"Event {event} processed for peer {peer_id}.",
            }
        ),
        200,
    )


@app.route("/list", methods=["GET"])
def list():
    # list of all registered peers
    peer_list = [
        {"peer_id": peer_id, "ip": peer_info["ip"], "port": peer_info["port"], "files": peer_info["files"]}
        for peer_id, peer_info in peers.items()
    ]
    
    # Return just the list of peers
    return jsonify(peer_list), 200


@app.route("/status", methods=["GET"])
def status():
    return (
        jsonify(
            {
                "tracker_id": tracker_id,
                "peers_count": len(peers),
                "files_count": len(files),
            }
        ),
        200,
    )

@app.route("/request", method="POST")
def handle_request(): #
    data = request.json
    info_hash = data.get("info_hash")
    peer_id = data.get("peer_id") #uuid
    port = data.get("port")
    uploaded = data.get("uploaded")
    downloaded = data.get("downloaded")
    left = data.get("left")

    if not all([info_hash, peer_id, port, uploaded, downloaded, left]):#missing para
        return jsonify({"status": "error", "message": "Missing required parameters."}), 400
    
    if info_hash not in files:
        return jsonify({"status": "error", "message": "Torrent not found."}), 404

    peer_list = [
        {"ip": peers[peer_id]["ip"], "port": peers[peer_id]["port"]}
        for peer_id in files[info_hash]["nodes"]
        if peer_id != peer_id  # Exclude the requesting peer 
    ]
    
    # Response { count_seeder, count_leecher, peers}
    count_seeder = sum(1 for peer_id in files[info_hash]["nodes"] if peers[peer_id]["left"] == 0)
    count_leecher = len(files[info_hash]["nodes"]) - count_seeder

    # Build the response
    response = {
        "status": "success",
        #"message": f"Peers for {info_hash} retrieved successfully.",
        #"tracker_id": tracker_id,  
        "count_seeder": count_seeder,
        "count_leecher": count_leecher,
        "peers": peer_list
    }

    return jsonify(response), 200

#parse file? 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
