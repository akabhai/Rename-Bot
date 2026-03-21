from flask import Flask, render_template_string
from helper.database import grant_unlimited
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Bot is Running!'

# 1. The Mini App Page (Uses your specific Monetag SDK)
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
        
        <!-- YOUR MONETAG SDK -->
        <script src='//libtl.com/sdk.js' data-zone='10759225' data-sdk='show_10759225'></script>
        
        <style>
            body { background: #0e1621; color: white; font-family: sans-serif; text-align: center; padding: 20px; }
            .card { background: #17212b; border-radius: 15px; padding: 30px; margin-top: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            .btn { background: #2481cc; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 18px; font-weight: bold; width: 100%; margin-top: 20px; cursor: pointer; }
            .btn:active { transform: scale(0.98); }
            h1 { font-size: 60px; margin: 10px 0; color: #64b5f6; }
            p { color: #8ba3b7; font-size: 14px; line-height: 1.5; }
            .status { font-weight: bold; color: #4caf50; display: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h3>Reward Program</h3>
            <p>Watch 3 ads to unlock <b>6 Hours</b> of unlimited renaming and bypass all limits!</p>
            <h1 id="count">0 / 3</h1>
            <p id="status_msg" class="status">Unlocking Access...</p>
            <button class="btn" id="adBtn" onclick="playAd()">Watch Ad to Progress</button>
        </div>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();
            
            // Get count from local phone storage (Low DB Load)
            let watched = parseInt(localStorage.getItem('ads_watched') || '0');
            
            function updateUI() {
                document.getElementById('count').innerText = watched + " / 3";
                if(watched >= 3) {
                    document.getElementById('adBtn').style.display = 'none';
                    document.getElementById('status_msg').style.display = 'block';
                }
            }

            function playAd() {
                // Triggering your specific Monetag function
                if (typeof show_10759225 === 'function') {
                    show_10759225().then(() => {
                        // Ad Finished Successfully
                        watched++;
                        localStorage.setItem('ads_watched', watched);
                        updateUI();

                        if (watched >= 3) {
                            // 3 Ads done! Ping Render API to update MongoDB
                            fetch('/api/grant/{{user_id}}')
                            .then(res => {
                                localStorage.setItem('ads_watched', '0'); // Reset local count
                                tg.showAlert("✅ Unlimited Access Granted for 6 Hours!");
                                tg.close();
                            });
                        } else {
                            tg.showAlert("Ad view recorded! Only " + (3 - watched) + " more to go.");
                        }
                    });
                } else {
                    tg.showAlert("Ad is still loading... please wait 3 seconds and click again.");
                }
            }
            updateUI();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_code, user_id=user_id)

# 2. The API to update user status in MongoDB
@app.route('/api/grant/<int:user_id>')
def api_grant(user_id):
    grant_unlimited(user_id) # Function from helper/database.py
    return {"status": "success"}, 200

if __name__ == "__main__":
    app.run()
