from flask import Flask, request, jsonify
from flask_cors import CORS  # Required to allow GitHub site to talk to Render
from pymongo import MongoClient
import time
import os

app = Flask(__name__)
# This allows your GitHub site (akapass.github.io) to send requests to this API
CORS(app)

# MongoDB Connection
DB_URL = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "TechifyBots")

client = MongoClient(DB_URL)
db = client[DB_NAME]
users = db["users"]

@app.route('/')
def index():
    return "✅ Verification Hub API is Online and Active!"

@app.route('/verify', methods=['GET', 'POST'])
def verify_callback():
    # Try to get UID from URL parameters (?uid=)
    user_id = request.args.get('uid')
    
    if not user_id:
        return jsonify({"status": "failed", "error": "No User ID provided"}), 400

    try:
        # Convert to Integer (Telegram IDs are numbers)
        uid_int = int(user_id)
        
        # Grant 6 Hours (21600 seconds)
        expiry_time = time.time() + 21600
        
        # Update MongoDB:
        # We use 'id' to match the helper/database.py 'find_one' logic
        users.update_one(
            {"id": uid_int}, 
            {"$set": {"unlimited_expiry": expiry_time}}, 
            upsert=True
        )
        
        return jsonify({
            "status": "success", 
            "message": "6h access granted",
            "user_id": uid_int,
            "expiry": expiry_time
        }), 200
        
    except ValueError:
        return jsonify({"status": "failed", "error": "Invalid User ID format"}), 400
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500

if __name__ == "__main__":
    # Render uses port 8080 by default for some templates, 
    # but Flask default is 5000. Port 8080 is safer for Render.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
