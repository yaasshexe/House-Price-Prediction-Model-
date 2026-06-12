"""
server/app.py
────────────────────────────────────────────────────────
Pune House Price Prediction — Flask API Server
Serves the prediction model via REST endpoints.

OJT Project — M.Sc. Data Science
Run:  python server/app.py
"""

import sys
import os
import json
from werkzeug.utils import secure_filename

# ── Make model folder importable ──────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from model.price_model import predict_price, LOCATION_PRICES, BHK_MULTIPLIERS

# ── Upload configuration ──────────────────────────────
UPLOAD_FOLDER = os.path.join(ROOT, "client", "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__, static_folder=os.path.join(ROOT, "client"), static_url_path="")
CORS(app)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

DATA_PATH = os.path.join(ROOT, "data", "locations.json")
with open(DATA_PATH) as f:
    LOCATION_DATA = json.load(f)["locations"]

LOCATION_MAP = {loc["id"]: loc for loc in LOCATION_DATA}


@app.route("/api/locations", methods=["GET"])
def get_locations():
    return jsonify({"locations": LOCATION_DATA})


# ── API: POST /api/predict ────────────────────────────
@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Expects JSON body:
    {
      "area":        1200,
      "location":    "baner",
      "bhk":         "2bhk",
      "floor":       5,
      "age":         2,
      "parking":     1,
      "gym":         1,
      "pool":        0,
      "clubhouse":   1,
      "security_24": 1,
      "power_backup":1
    }
    """
    try:
        body = request.get_json(force=True)

        # ── Validate required fields ───────────────────
        required = ["area", "location", "bhk"]
        for field in required:
            if field not in body:
                return jsonify({"error": f"Missing field: {field}"}), 400

        area     = int(body["area"])
        location = str(body["location"])
        bhk      = str(body["bhk"])

        if area < 200 or area > 10000:
            return jsonify({"error": "Area must be between 200 and 10000 sq ft"}), 400
        if location not in LOCATION_PRICES:
            return jsonify({"error": f"Unknown location: {location}"}), 400
        if bhk not in BHK_MULTIPLIERS:
            return jsonify({"error": f"Unknown BHK type: {bhk}"}), 400

        # ── Optional amenity fields (default sensible) ─
        floor        = int(body.get("floor", 5))
        age          = int(body.get("age", 0))
        parking      = int(body.get("parking", 1))
        gym          = int(body.get("gym", 0))
        pool         = int(body.get("pool", 0))
        clubhouse    = int(body.get("clubhouse", 0))
        security_24  = int(body.get("security_24", 1))
        power_backup = int(body.get("power_backup", 1))

        # ── Run prediction ─────────────────────────────
        result = predict_price(
            area=area, location=location, bhk=bhk,
            floor=floor, age=age, parking=parking,
            gym=gym, pool=pool, clubhouse=clubhouse,
            security_24=security_24, power_backup=power_backup
        )

        # ── Attach location metadata ───────────────────
        loc_meta = LOCATION_MAP.get(location, {})
        result["location_meta"] = {
            "name":         loc_meta.get("name", location),
            "zone":         loc_meta.get("zone", ""),
            "tier":         loc_meta.get("tier", ""),
            "amenities":    loc_meta.get("amenities", []),
            "description":  loc_meta.get("description", ""),
            "connectivity": loc_meta.get("connectivity", ""),
            "appreciation": loc_meta.get("appreciation", ""),
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: GET /api/health ──────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Pune House Price API is running"})


# ── API: POST /api/upload-background ───────────────────
@app.route("/api/upload-background", methods=["POST"])
def upload_background():
    """Upload background image for the app."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP"}), 400
        
        if len(file.read()) > MAX_FILE_SIZE:
            file.seek(0)
            return jsonify({"error": f"File too large. Max size: 5MB"}), 400
        
        file.seek(0)
        filename = secure_filename("background_" + file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        return jsonify({
            "success": True,
            "message": "Background image uploaded successfully",
            "url": f"/uploads/{filename}"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: GET /uploads/<filename> ───────────────────────
@app.route("/uploads/<filename>", methods=["GET"])
def get_upload(filename):
    """Serve uploaded files."""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except:
        return jsonify({"error": "File not found"}), 404


# ── API: GET /api/background ──────────────────────────
@app.route("/api/background", methods=["GET"])
def get_background():
    """Get list of available background images."""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({"images": []})
        
        images = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
        return jsonify({
            "images": images,
            "paths": [f"/uploads/{img}" for img in images]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Start ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🏠  Pune House Price Prediction Server")
    print("━" * 42)
    print(f"   Root     : {ROOT}")
    print(f"   Client   : {app.static_folder}")
    print(f"   API base : http://127.0.0.1:5000/api")
    print(f"   App URL  : http://127.0.0.1:5000")
    print("━" * 42 + "\n")
    app.run(debug=True, port=5000)
