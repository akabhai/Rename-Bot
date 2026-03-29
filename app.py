from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import time
import os

app = Flask(__name__)
CORS(app)

# MongoDB Configuration - MATCHING YOUR DATABASE.PY
DB_URL = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "TechifyBots")
client = MongoClient(DB_URL)
db = client[DB_NAME]
dbcol = db["user"] # MATCHES database.py collection name

@app.route('/')
def index():
    return "✅ Renamer Verification Hub is Online"

@app.route('/verify', methods=['GET', 'POST'])
def verify_callback():
    user_id = request.args.get('uid')
    if not user_id:
        return jsonify({"status": "failed"}), 400

    # 1. Convert to Int
    uid_int = int(user_id)
    expiry_time = int(time.time()) + 21600 # 6 Hours
    
    # 2. Update 'user' collection (Singular) and field 'unlimited_expiry'
    dbcol.update_one(
        {"_id": uid_int}, 
        {"$set": {"unlimited_expiry": expiry_time}}, 
        upsert=True
    )
    return jsonify({"status": "success"}), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
