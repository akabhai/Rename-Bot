from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import time
import os

app = Flask(__name__)
# This allows GitHub Pages to communicate with your Render app
CORS(app)

# MongoDB Connection
DB_URL = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "TechifyBots")

try:
    client = MongoClient(DB_URL)
    db = client[DB_NAME]
    # Important: your database.py uses "user" not "users"
    dbcol = db["user"] 
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route('/')
def index():
    return "✅ Renamer Verification API is Running!"

@app.route('/verify', methods=['GET', 'POST'])
def verify_callback():
    user_id = request.args.get('uid')
    
    if not user_id:
        return jsonify({"status": "failed", "error": "No User ID provided"}), 400

    try:
        uid_int = int(user_id)
        # Grant 6 Hours (21600 seconds)
        expiry_time = int(time.time()) + 21600
        
        # Update MongoDB: Match your bot's database structure (_id)
        dbcol.update_one(
            {"_id": uid_int}, 
            {"$set": {"unlimited_expiry": expiry_time}}, 
            upsert=True
        )
        
        return jsonify({"status": "success", "message": "6h access granted"}), 200
    except ValueError:
        return jsonify({"status": "failed", "error": "Invalid User ID"}), 400
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
