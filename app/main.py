from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import re
import os

# --- Configure Gemini ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app)  # Add this for Android CORS support

# Add max file size configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route("/analyze", methods=["POST"])
def analyze_leaf():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        image_file = request.files["image"]
        
        # Check if file is empty
        if image_file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        image_data = image_file.read()

        # Structured prompt
        prompt = """
        You are an agricultural advisor for Indian farmers.
        Analyze this plant leaf image and respond ONLY in valid JSON.
        Do NOT include markdown, extra text, or explanations.
        Keep the language simple and farmer-friendly.
        JSON format must be:
        {
          "disease": "Name of disease or 'Healthy'",
          "description": "1-2 lines describing the disease",
          "cure": "How to cure the disease"
        }
        """

        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ])

        raw_text = response.text.strip()

        # Clean out accidental markdown/code fences
        raw_text = re.sub(r"```[a-zA-Z]*", "", raw_text).replace("```", "").strip()

        try:
            result_json = json.loads(raw_text)
        except Exception:
            result_json = {
                "disease": "Parsing Error",
                "description": raw_text[:200],
                "cure": "Not available"
            }

        return jsonify(result_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
