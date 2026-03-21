from flask import Flask, render_template_string
from helper.database import grant_unlimited
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# Replace '8888888' with your actual Monetag Zone ID
MONETAG_ZONE_ID = "8888888" 

@app.route('/')
def hello_world():
    return 'Bot is Running!'

# 1. The Mini App Page (Users watch ads here)
@app.route('/ads/<int:user_id>')
def ads_page(user_id):
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unlock Unlimited</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://alwingulla.com/88/tag.min.js" data-zone="{{zone_id}}" async data-no-optimize="1" data-cfasync="false"></script>
        <style>
            body { background: #0e1621; color: white; font-family: sans-serif; text-align: center; padding: 20px; }
            .card { background: #17212b; border-radius: 15px; padding: 30px; margin-top: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
            .btn { background: #2481cc; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; width: 100%; margin-top: 20px; }
            .btn:disabled { background: #555; cursor: not-allowed; }
            h1 { font-size: 40px; margin: 10px 0; color: #64b5f6; }
            p { color: #8ba3b7; line-height: 1.5; }
        </style>
    </head>
    <body>
        <div class="card">
            <h3>Reward Program</h3>
            <p>Watch 3 ads to unlock <b>6 Hours</b> of unlimited renaming!</p>
            <h1 id="count">0 / 3</h1>
            <button class="btn" id="adBtn" onclick="showAd()">Watch Ad</button>
        </div>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();
            let watched = parseInt(localStorage.getItem('ads_watched') || '0');
            
            function updateUI() {
                document.getElementById('count').innerText = watched + " / 3";
                if(watched >= 3) {
                    document.getElementById('adBtn').innerText = "Unlocking...";
                    document.getElementById('adBtn').disabled = true;
                }
            }

            function showAd() {
                // This triggers the Monetag interstitial
                if (typeof show_{{zone_id}} === 'function') {
                    show_{{zone_id}}().then(() => {
                        watched++;
                        localStorage.setItem('ads_watched', watched);
                        updateUI();

                        if (watched >= 3) {
                            // Call backend to grant 6 hours
                            fetch('/api/grant/{{user_id}}')
                            .then(res => {
                                localStorage.setItem('ads_watched', '0');
                                tg.showAlert("✅ Success! 6 Hours Unlimited access granted.");
                                tg.close();
                            });
                        }
                    });
                } else {
                    tg.showAlert("Ad is loading... Please wait 3 seconds.");
                }
            }
            updateUI();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_code, user_id=user_id, zone_id=MONETAG_ZONE_ID)

# 2. The API to update MongoDB
@app.route('/api/grant/<int:user_id>')
def api_grant(user_id):
    grant_unlimited(user_id)
    return {"status": "success"}, 200

if __name__ == "__main__":
    app.run()
