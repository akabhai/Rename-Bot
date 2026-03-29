from flask import Flask, request
from pymongo import MongoClient
import time
import os

app = Flask(__name__)

# MongoDB Connection
DB_URL = os.environ.get("DATABASE_URL", "")
client = MongoClient(DB_URL)
db = client["TechifyBots"] # Ensure this matches your DB name
users = db["users"]

@app.route('/')
def index():
    return "Renamer Bot Verification API is Running"

@app.route('/verify')
def verify_callback():
    user_id = request.args.get('uid')
    
    if not user_id:
        return {"status": "failed", "error": "No User ID provided"}, 400

    # Grant 6 Hours (21600 seconds)
    expiry_time = time.time() + 21600
    
    # Update MongoDB: Use 'id' to match your bot's database structure
    users.update_one(
        {"id": int(user_id)}, 
        {"$set": {"unlimited_expiry": expiry_time}}, 
        upsert=True
    )
    
    return {"status": "success", "message": "6h access granted"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
