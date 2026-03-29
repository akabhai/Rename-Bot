from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import time
import os

app = Flask(__name__)
CORS(app) # Allows GitHub to talk to Render

# MongoDB Configuration
DB_URL = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "TechifyBots")
client = MongoClient(DB_URL)
db = client[DB_NAME]
users = db["users"]

@app.route('/')
def index():
    return "Bot Verification API is Running"

@app.route('/verify', methods=['GET', 'POST'])
def verify_callback():
    # Get UID from query params
    user_id = request.args.get('uid')
    
    if not user_id:
        return jsonify({"status": "failed", "error": "No User ID"}), 400

    try:
        # 1. Convert to Integer (Telegram IDs are numbers)
        uid_int = int(user_id)
        
        # 2. Calculate Expiry (Now + 6 Hours)
        expiry_time = time.time() + 21600
        
        # 3. Update MongoDB
        # We use {"id": uid_int} because your renamer bot uses "id" field
        users.update_one(
            {"id": uid_int}, 
            {"$set": {"unlimited_expiry": expiry_time}}, 
            upsert=True
        )
        
        return jsonify({
            "status": "success", 
            "message": "6h access granted",
            "expiry": expiry_time
        }), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
