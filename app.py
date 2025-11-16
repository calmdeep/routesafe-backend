# app.py - Flask Backend with Image Verification
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import base64
import json
from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)

client = anthropic.Anthropic()

@app.route('/api/verify-image', methods=['POST'])
def verify_image():
    """Verify if uploaded image is a road/street image"""
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'isValid': False, 'reason': 'No image provided'}), 400
        
        # Extract base64 image data
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Determine image type
        media_type = 'image/jpeg'
        if data.get('image', '').startswith('data:image/png'):
            media_type = 'image/png'
        
        # Call Claude API for verification
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
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
                        "text": """Analyze this image quickly and determine if it could be related to roads or outdoor surfaces.

Return ONLY a JSON object (no markdown, no backticks):

{
  "isValid": true or false,
  "reason": "brief explanation"
}

ACCEPT these images:
- Any roads, highways, streets (clear or unclear)
- Parking lots, driveways, sidewalks
- ANY outdoor paved surface
- Even blurry road images
- Even partial road views
- Ground/pavement from any angle

REJECT only these:
- Clear portraits/selfies of people
- Indoor scenes with no outdoor elements
- Animals close-up
- Food items
- Pure text documents

Be VERY LENIENT - when in doubt, accept the image."""
                    }
                ]
            }]
        )
        
        response_text = message.content[0].text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(response_text)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Verification Error: {str(e)}")
        return jsonify({
            'isValid': False,
            'reason': 'Failed to verify image. Please try again.'
        }), 500

@app.route('/api/detect', methods=['POST'])
def detect_potholes():
    """Detect potholes in verified road images"""
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
                        "text": """You are an expert road damage detection AI. Analyze this road image with MAXIMUM ACCURACY for potholes, cracks, and structural damage.

Return ONLY a valid JSON object (no markdown, no backticks) with this structure:

{
  "hasPotholes": true or false,
  "totalPotholes": exact number,
  "detections": [
    {
      "id": number,
      "severity": "HIGH" or "MEDIUM" or "LOW",
      "confidence": decimal 0-1,
      "location": "precise location description",
      "estimatedSize": "small" or "medium" or "large",
      "damageType": "pothole" or "crack" or "surface damage",
      "estimatedDepth": "shallow" or "moderate" or "deep",
      "description": "technical description"
    }
  ],
  "roadType": "National Highway" or "State Highway" or "District Road" or "Urban Road" or "Rural Road",
  "roadCondition": "Excellent" or "Good" or "Fair" or "Poor" or "Very Poor",
  "overallRiskLevel": "Critical" or "High" or "Moderate" or "Low"
}

CRITICAL RULES:
- BE EXTREMELY ACCURATE - Only report actual visible damage
- Look for: potholes, cracks, worn surfaces, edge breaks, depressions
- Severity HIGH = immediate safety risk (large/deep)
- Severity MEDIUM = needs attention soon
- Severity LOW = minor wear
- Provide precise location details
- Be conservative with confidence scores"""
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
    print("🚀 RouteSafe Backend Starting...")
    print("📍 Running on: http://localhost:5000")
    print("✅ Image verification enabled")
    print("✅ Ready to receive requests")
    app.run(debug=True, host='0.0.0.0', port=5000)
