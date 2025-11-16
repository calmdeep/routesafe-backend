# app.py - Flask Backend WITHOUT Image Verification
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json

app = Flask(__name__)
CORS(app)

client = anthropic.Anthropic()

@app.route('/api/verify-image', methods=['POST'])
def verify_image():
    """Always returns valid - no verification"""
    return jsonify({
        'isValid': True,
        'reason': 'Image accepted'
    })

@app.route('/api/detect', methods=['POST'])
def detect_potholes():
    """Detect potholes in road images"""
    try:
        data = request.json
        image_data = data.get('image')
        location = data.get('location', {})
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        # Extract base64 image data
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Determine image type
        media_type = 'image/jpeg'
        if data.get('image', '').startswith('data:image/png'):
            media_type = 'image/png'
        
        # Call Claude API for detection
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
                        "text": """You are an expert road damage detection AI. Analyze this image for potholes, cracks, and road damage.

Return ONLY a valid JSON object (no markdown, no backticks):

{
  "hasPotholes": true or false,
  "totalPotholes": number,
  "detections": [
    {
      "id": number,
      "severity": "HIGH" or "MEDIUM" or "LOW",
      "confidence": number between 0 and 1,
      "location": "description of location in image",
      "estimatedSize": "small" or "medium" or "large",
      "damageType": "pothole" or "crack" or "surface damage",
      "estimatedDepth": "shallow" or "moderate" or "deep",
      "description": "brief technical description"
    }
  ],
  "roadType": "National Highway" or "State Highway" or "District Road" or "Urban Road" or "Rural Road",
  "roadCondition": "Excellent" or "Good" or "Fair" or "Poor" or "Very Poor",
  "overallRiskLevel": "Critical" or "High" or "Moderate" or "Low"
}

IMPORTANT:
- If you see a road/pavement with damage, set hasPotholes to true
- If you see a clear road with NO damage, set hasPotholes to false and totalPotholes to 0
- Be accurate but not too strict
- Look for visible potholes, cracks, worn surfaces
- HIGH severity = dangerous/large damage
- MEDIUM severity = needs attention
- LOW severity = minor wear"""
                    }
                ]
            }]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(response_text)
        
        # Sort detections by severity
        if result.get('detections'):
            severity_order = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            result['detections'].sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        # Add location data
        result['location'] = location
        result['success'] = True
        
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Response was: {response_text}")
        return jsonify({
            'success': False,
            'error': 'Failed to parse AI response',
            'raw_response': response_text[:500]
        }), 500
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'RouteSafe Backend Running'}), 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🚀 RouteSafe Backend Starting...")
    print("📍 Running on port:", port)
    print("✅ Image verification DISABLED - All images accepted")
    print("✅ Ready to receive requests")
    app.run(debug=False, host='0.0.0.0', port=port)
