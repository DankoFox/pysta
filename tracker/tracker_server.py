from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# In-memory data structures
peers = {}  # {peer_id: {"ip": str, "port": int, "files": [file_names]}}
files = {}  # {file_name: {"nodes": [peer_ids]}}
tracker_id = str(uuid.uuid4())  # Unique tracker ID


@app.route("/register", methods=["POST"])
@app.route("/register", methods=["POST"])
def register():
    """
    Register a peer with the tracker, including its files and details.
    """
    data = request.json

    # Validate input data
    required_fields = {"peer_id", "ip", "port", "files"}
    if not required_fields.issubset(data.keys()):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    peer_id = data["peer_id"]
    ip = data["ip"]
    port = data["port"]
    files_list = data["files"]

    # Register peer and files
    peers[peer_id] = {"ip": ip, "port": port, "files": files_list}
    for file_metadata in files_list:
        file_name = file_metadata["file_name"]  # Extract file_name from metadata
        if file_name not in files:
            files[file_name] = {"nodes": []}
        if peer_id not in files[file_name]["nodes"]:
            files[file_name]["nodes"].append(peer_id)

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
    """
    Query the tracker for peers sharing a specific file.
    """
    file_queried = request.args.get("file_name")
    if not file_queried or file_queried not in files:
        return jsonify({"status": "error", "message": "File not found."}), 404

    # Get peer details sharing the file
    node_details = [
        {"peer_id": peer_id, "ip": peers[peer_id]["ip"], "port": peers[peer_id]["port"]}
        for peer_id in files[file_queried]["nodes"]
    ]

    return jsonify({"status": "success", "nodes": node_details}), 200


@app.route("/update", methods=["POST"])
def update():
    """
    Update file sharing status for a peer (started, stopped, or completed).
    """
    data = request.json

    # Validate input data
    required_fields = {"peer_id", "file_name", "event"}
    if not required_fields.issubset(data.keys()):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    peer_id = data["peer_id"]
    file_name = data["file_name"]
    event = data["event"]

    if peer_id not in peers or file_name not in files:
        return jsonify({"status": "error", "message": "Invalid peer or file."}), 400

    # Handle the event
    if event == "started":
        if peer_id not in files[file_name]["nodes"]:
            files[file_name]["nodes"].append(peer_id)
    elif event == "stopped":
        if peer_id in files[file_name]["nodes"]:
            files[file_name]["nodes"].remove(peer_id)
    elif event == "completed":
        # Optional logic for completed event
        pass

    return (
        jsonify(
            {
                "status": "success",
                "message": f"Event '{event}' processed for peer {peer_id}.",
            }
        ),
        200,
    )


@app.route("/deregister", methods=["POST"])
@app.route("/deregister", methods=["POST"])
def deregister():
    """
    Deregister a peer and remove its file associations.
    """
    data = request.json

    # Validate input data
    required_fields = {"peer_id"}
    if not required_fields.issubset(data.keys()):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    peer_id = data["peer_id"]

    if peer_id not in peers:
        return jsonify({"status": "error", "message": "Peer not found."}), 404

    # Remove the peer from all associated files
    for file_metadata in peers[peer_id]["files"]:
        file_name = file_metadata["file_name"]  # Extract file_name from metadata
        if file_name in files and peer_id in files[file_name]["nodes"]:
            files[file_name]["nodes"].remove(peer_id)
            # Remove the file entry if no peers are sharing it
            if not files[file_name]["nodes"]:
                del files[file_name]

    # Remove the peer
    del peers[peer_id]
    return (
        jsonify(
            {
                "status": "success",
                "message": f"Peer {peer_id} deregistered successfully.",
            }
        ),
        200,
    )


@app.route("/status", methods=["GET"])
def status():
    """
    Get tracker status, including peer and file counts.
    """
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969)
