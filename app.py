from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import base64

app = Flask(__name__)

# CORS FIX FOR VERCEL FRONTEND
CORS(app, resources={r"/*": {"origins": "*"}})

# === Roboflow Model Credentials ===
ROBOFLOW_API_KEY = os.environ.get("rf_YGfI1uPHeBZ2NoazegJoAgCnbyJ3")
ROBOFLOW_MODEL = "pothole-detection"   # change to your model name
ROBOFLOW_VERSION = "1"                 # change to your version


@app.route("/", methods=["POST"])
def handle_request():
    data = request.json
    image = data.get("image")
    location = data.get("location")

    if not image:
        return jsonify({"success": False, "error": "No image"}), 400

    # If only image (verification)
    if location is None:
        return jsonify({"isValid": True, "reason": "Image accepted"})

    # Extract raw base64
    if "," in image:
        base64_img = image.split(",")[1]
    else:
        base64_img = image

    # === ROB0FLOW API CALL ===
    url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}?api_key={ROBOFLOW_API_KEY}"

    try:
        rf_response = requests.post(
            url,
            data=base64.b64decode(base64_img),
            headers={"Content-Type": "application/octet-stream"}
        ).json()

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    # Convert Roboflow predictions → your JSON format
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
        "roadCondition": "Poor" if len(detections) else "Good",
        "overallRiskLevel": "HIGH" if len(detections) >= 3 else "LOW"
    }

    return jsonify(output)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


# REQUIRED FOR RENDER! (Fixes 100% of “server not connecting” issues)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
