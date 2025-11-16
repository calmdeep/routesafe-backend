from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import base64

app = Flask(__name__)
CORS(app)

# === Roboflow Credentials ===
ROBOFLOW_API_KEY = os.environ.get("rf_YGfI1uPHeBZ2NoazegJoAgCnbyJ3")  # or paste directly
ROBOFLOW_MODEL = "pothole-detection"   # example
ROBOFLOW_VERSION = "1"                 # example


@app.route("/", methods=["POST"])
def handle_request():
    data = request.json
    image = data.get("image")
    location = data.get("location")

    if not image:
        return jsonify({"success": False, "error": "No image"}), 400

    # Verification request (only image check)
    if location is None:
        return jsonify({"isValid": True, "reason": "Image accepted"})

    # Extract base64 content
    if "," in image:
        base64_img = image.split(",")[1]
    else:
        base64_img = image

    # === Send image to Roboflow ===
    url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}?api_key={ROBOFLOW_API_KEY}"

    try:
        rf_response = requests.post(
            url,
            data=base64.b64decode(base64_img),
            headers={"Content-Type": "application/octet-stream"}
        ).json()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    # === Convert Roboflow result → Your frontend JSON format ===
    detections = []
    for idx, pred in enumerate(rf_response.get("predictions", [])):
        detections.append({
            "id": idx + 1,
            "severity": "HIGH" if pred["confidence"] > 0.85 else "MEDIUM",
            "confidence": round(pred["confidence"], 3),
            "damageType": "pothole",
            "estimatedSize": "large" if pred["width"] > 100 else "medium",
            "description": f"Pothole detected at ({pred['x']}, {pred['y']})"
        })

    output = {
        "success": True,
        "location": location,
        "hasPotholes": len(detections) > 0,
        "totalPotholes": len(detections),
        "detections": detections,
        "roadType": "Unknown",
        "roadCondition": "Poor" if len(detections) > 0 else "Good",
        "overallRiskLevel": "HIGH" if len(detections) >= 3 else "LOW"
    }

    return jsonify(output)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})
