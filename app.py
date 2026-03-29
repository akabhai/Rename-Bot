from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import time
import os

app = Flask(__name__)
# This allows your GitHub site to talk to this Render API
CORS(app)

# MongoDB Connection Logic
DB_URL = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "TechifyBots")

try:
    client = MongoClient(DB_URL)
    db = client[DB_NAME]
    dbcol = db["user"] # MATCHES your database.py collection name
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route('/')
def index():
    return "✅ Verification Hub API is Online!"

@app.route('/verify', methods=['GET', 'POST'])
def verify_callback():
    # 1. Get User ID from URL parameter
    user_id = request.args.get('uid')
    
    if not user_id:
        return jsonify({"status": "failed", "error": "No User ID"}), 400

    try:
        uid_int = int(user_id)
        # Calculate 6 Hours expiry
        expiry_time = int(time.time()) + 21600
        
        # 2. Update MongoDB using the exact format from your database.py
        # We use _id because your bot checks find_one({"_id": id})
        dbcol.update_one(
            {"_id": uid_int}, 
            {"$set": {"unlimited_expiry": expiry_time}}, 
            upsert=True
        )
        
        return jsonify({
            "status": "success", 
            "message": "Access granted for 6h",
            "user_id": uid_int
        }), 200
        
    except ValueError:
        return jsonify({"status": "failed", "error": "Invalid User ID format"}), 400
    except Exception as err:
        return jsonify({"status": "failed", "error": str(err)}), 500

if __name__ == "__main__":
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
