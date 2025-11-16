import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MODEL_ID = "pothole-detection-2"
VERSION_ID = "2"
API_KEY = "rf_YGfI1uPHeBZ2NoazegJoAgCnbyJ3"

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json
    image_b64 = data.get("image")

    if not image_b64:
        return jsonify({"error": "no image"}), 400

    # Roboflow expects CLEAN base64, not DataURL
    if image_b64.startswith("data:image"):
        image_b64 = image_b64.split(",")[1]

    url = f"https://detect.roboflow.com/{pothole-detection-2}/{2}"

    response = requests.post(
        url,
        params={"api_key": rf_YGfI1uPHeBZ2NoazegJoAgCnbyJ3},
        data=base64.b64decode(image_b64),
        headers={"Content-Type": "application/octet-stream"}
    )

    return jsonify(response.json())
