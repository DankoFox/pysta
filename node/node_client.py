# import requests
# from flask import Flask, request, jsonify

# #app = Flask(__name__)

# def send_request_to_tracker(tracker_url, info_hash, peer_id, port, uploaded, downloaded, left):
#     # Build the request payload
#     request_data = {
#         "info_hash": info_hash,
#         "peer_id": peer_id,
#         "port": port,
#         "uploaded": uploaded,
#         "downloaded": downloaded,
#         "left": left
#     }

#     # Send the request to the tracker
#     try:
#         response = requests.post(tracker_url, json=request_data)
#         if response.status_code == 200:
#             # Parse the tracker response
#             response_data = response.json()
#             print("Tracker Response:", response_data)
#             return response_data
#         else:
#             print(f"Error: {response.status_code}, {response.text}")
#             return None
#     except requests.RequestException as e:
#         print("Failed to connect to tracker:", e)
#         return None


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)