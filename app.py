from flask import Flask, request, jsonify
from flask_cors import CORS
import google.genai as genai
import json
import os

app = Flask(__name__)
CORS(app)

# Load API Key
genai_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=genai_key)

@app.route('/', methods=['POST'])
def handle_request():
    data = request.json
    image = data.get("image")
    location = data.get("location")

    if not image:
        return jsonify({"success": False, "error": "No image"}), 400

    # Verification request (only image)
    if location is None:
        return jsonify({"isValid": True, "reason": "Image accepted"})

    # Extract base64
    if "," in image:
        base64_img = image.split(",")[1]
    else:
        base64_img = image

    # Send to Gemini Flash Vision
    prompt = """
You are a road damage detection AI. Analyze image and return *ONLY JSON*:

{
  "hasPotholes": true/false,
  "totalPotholes": number,
  "detections": [
    {
      "id": number,
      "severity": "HIGH" | "MEDIUM" | "LOW",
      "confidence": float,
      "damageType": "pothole" | "crack" | "surface damage",
      "estimatedSize": "small" | "medium" | "large",
      "description": "text"
    }
  ],
  "roadType": "...",
  "roadCondition": "...",
  "overallRiskLevel": "..."
}
"""

    response = client.models.generate(
        model="gemini-2.0-flash-vision",
        prompt=prompt,
        image=[{
            "mime_type": "image/jpeg",
            "data": base64_img
        }]
    )

    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
    except:
        return jsonify({"success": False, "error": "Invalid JSON", "raw": text}), 500

    result["location"] = location
    result["success"] = True
    return jsonify(result)


@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})
