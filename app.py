from flask import Flask, render_template_string
from helper.database import grant_unlimited
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# Replace this with your actual Monetag (or any ad network) DIRECT LINK
DIRECT_AD_LINK = "https://your-direct-link-url.com" 

@app.route('/')
def hello_world():
    return 'Bot is Running!'

# 1. The Mini App Page (Uses Direct Link instead of SDK)
@app.route('/ads/<int:user_id>')
def ads_page(user_id):
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Unlock Unlimited Access</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        
        <style>
            body { background: #0e1621; color: white; font-family: sans-serif; text-align: center; padding: 20px; }
            .card { background: #17212b; border-radius: 15px; padding: 30px; margin-top: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            .btn { background: #2481cc; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 18px; font-weight: bold; width: 100%; margin-top: 20px; cursor: pointer; transition: 0.3s; }
            .btn:active { transform: scale(0.98); }
            .btn:disabled { background: #555; cursor: not-allowed; }
            h1 { font-size: 60px; margin: 10px 0; color: #64b5f6; }
            p { color: #8ba3b7; font-size: 14px; line-height: 1.5; }
            .status { font-weight: bold; color: #4caf50; display: none; margin-top: 20px; font-size: 18px;}
        </style>
    </head>
    <body>
        <div class="card">
            <h3>Reward Program</h3>
            <p>Click the ad link <b>4 times</b> to unlock <b>6 Hours</b> of unlimited renaming and bypass all limits!</p>
            <h1 id="count">0 / 4</h1>
            <p id="status_msg" class="status">Unlocking Access... Please Wait.</p>
            <button class="btn" id="adBtn" onclick="playAd()">Open Ad Link</button>
        </div>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();
            
            // Get count from local phone storage (Low DB Load)
            let clicked = parseInt(localStorage.getItem('link_clicks') || '0');
            const directLink = "{{direct_link}}";
            
            function updateUI() {
                document.getElementById('count').innerText = clicked + " / 4";
                if(clicked >= 4) {
                    document.getElementById('adBtn').style.display = 'none';
                    document.getElementById('status_msg').style.display = 'block';
                    
                    // 4 Clicks done! Ping Render API to update MongoDB
                    fetch('/api/grant/{{user_id}}')
                    .then(res => {
                        localStorage.setItem('link_clicks', '0'); // Reset local count
                        tg.showAlert("✅ Unlimited Access Granted for 6 Hours!");
                        setTimeout(() => tg.close(), 1500); // Close TMA automatically
                    }).catch(err => {
                        tg.showAlert("❌ Error verifying access. Please try again.");
                    });
                }
            }

            function playAd() {
                if (clicked >= 4) return;

                // 1. Open the Direct Link safely inside Telegram
                tg.openLink(directLink);
                
                // 2. Increment the click counter
                clicked++;
                localStorage.setItem('link_clicks', clicked);
                
                // 3. Disable button for 5 seconds to prevent spam clicking
                let btn = document.getElementById('adBtn');
                btn.disabled = true;
                let timer = 5;
                btn.innerText = `Please wait ${timer}s...`;
                
                let countdown = setInterval(() => {
                    timer--;
                    if (timer > 0) {
                        btn.innerText = `Please wait ${timer}s...`;
                    } else {
                        clearInterval(countdown);
                        btn.disabled = false;
                        btn.innerText = "Open Ad Link Again";
                        updateUI(); // Refresh UI and check if goal is reached
                    }
                }, 1000);
            }
            
            // Initialize UI on load
            updateUI();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_code, user_id=user_id, direct_link=DIRECT_AD_LINK)

# 2. The API to update user status in MongoDB
@app.route('/api/grant/<int:user_id>')
def api_grant(user_id):
    grant_unlimited(user_id) # Function from helper/database.py
    return {"status": "success"}, 200

if __name__ == "__main__":
    app.run()
