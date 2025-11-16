# app.py – Unified Endpoint Backend for RouteSafe (works with your current frontend)
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json

app = Flask(__name__)
CORS(app)

client = anthropic.Anthropic()

@app.route('/', methods=['POST'])
def handle_request():
    """Auto-detect action: verify or detect"""

    try:
        data = request.json
        image_data = data.get('image')
        location = data.get('location')

        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        # ---------- CASE 1: IMAGE VERIFICATION ----------
        # Frontend sends only { image } for verifying
        if location is None:
            return jsonify({
                'isValid': True,
                'reason': 'Image accepted'
            })

        # ---------- CASE 2: DAMAGE DETECTION ----------
        # Frontend sends { image, location } for detection

        # Extract base64 data
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        # Determine image type
        media_type = "image/jpeg"
        if data.get("image", "").startswith("data:image/png"):
            media_type = "image/png"

        # Call Claude Vision API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": """
You are an expert road damage detection AI. Analyze this image for potholes, cracks, and surface damages.

Return ONLY a JSON object with the format:

{
  "hasPotholes": true or false,
  "totalPotholes": number,
  "detections": [
    {
      "id": number,
      "severity": "HIGH" | "MEDIUM" | "LOW",
      "confidence": float (0–1),
      "estimatedSize": "small" | "medium" | "large",
      "damageType": "pothole" | "crack" | "surface damage",
      "description": "brief description"
    }
  ],
  "roadType": "...",
  "roadCondition": "...",
  "overallRiskLevel": "..."
}
"""
                    }
                ]
            }]
        )

        # Parse JSON response
        response_text = message.content[0].text.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()

        result = json.loads(response_text)

        # Sort by severity
        if result.get("detections"):
            severity_order = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            result["detections"].sort(key=lambda x: severity_order.get(x["severity"], 4))

        # Add extra fields
        result["location"] = location
        result["success"] = True

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "error": "Failed to parse AI response",
            "raw_response": response_text[:500]
        }), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "RouteSafe Backend Running"})


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
