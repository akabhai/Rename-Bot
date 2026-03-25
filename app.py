from flask import Flask, render_template_string
from helper.database import grant_unlimited
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# The Direct Link/Smartlink you provided
DIRECT_AD_LINK = "https://omg10.com/4/10784312"

@app.route('/')
def hello_world():
    return 'Bot is Running!'

# 1. The Mini App Page (Serves your beautiful UI)
@app.route('/ads/<int:user_id>')
def ads_page(user_id):
    html_code = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Unlock Access</title>

        <!-- Telegram WebApp SDK -->
        <script src="https://telegram.org/js/telegram-web-app.js"></script>

        <style>
            :root {
                --bg-color: var(--tg-theme-bg-color, #0f172a);
                --text-color: var(--tg-theme-text-color, #ffffff);
                --hint-color: var(--tg-theme-hint-color, #94a3b8);
                --card-bg: var(--tg-theme-secondary-bg-color, #1e293b);
                --btn-color: var(--tg-theme-button-color, #3b82f6);
                --btn-text: var(--tg-theme-button-text-color, #ffffff);
            }

            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, sans-serif; }

            body {
                background-color: var(--bg-color);
                color: var(--text-color);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                width: 100%;
                max-width: 400px;
                background-color: var(--card-bg);
                padding: 30px 25px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }

            .icon { font-size: 50px; margin-bottom: 15px; }

            h1 { font-size: 22px; margin-bottom: 10px; font-weight: 700; }

            .instruction {
                background: rgba(59, 130, 246, 0.1);
                color: #60a5fa;
                padding: 12px;
                border-radius: 12px;
                font-size: 14px;
                margin-bottom: 20px;
                line-height: 1.4;
                border: 1px dashed #3b82f6;
            }

            .progress-wrapper {
                width: 100%;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
                height: 10px;
                margin-bottom: 10px;
                overflow: hidden;
            }

            .progress-fill {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6);
                transition: width 0.4s ease;
            }

            .step-text {
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 25px;
                color: var(--hint-color);
            }

            .btn {
                width: 100%;
                padding: 16px;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                background-color: var(--btn-color);
                color: var(--btn-text);
                transition: 0.2s;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            }

            .btn:active { transform: scale(0.97); }
            .btn:disabled { opacity: 0.5; cursor: not-allowed; }

            .success {
                color: #10b981;
                margin-top: 20px;
                font-weight: bold;
                display: none;
                padding: 15px;
                background: rgba(16, 185, 129, 0.1);
                border-radius: 12px;
            }
        </style>
    </head>
    <body>

    <div class="container">
        <div class="icon">🔓</div>
        <h1>Unlock 6 Hours Access</h1>
        
        <div class="instruction">
            Click the button below and you will be redirected to our sponsor site. 
            <b>Wait for the page to load, then press BACK to return here.</b>
        </div>

        <div class="progress-wrapper">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div id="stepCounter" class="step-text">Steps Completed: 0 / 4</div>

        <button class="btn" id="actionBtn" onclick="handleVisit()">🚀 VISIT SPONSOR (Step 1)</button>

        <div class="success" id="successMsg">
            ✅ <b>Success!</b> 6 Hours Unlimited Unlocked.<br>Return to the bot now.
        </div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();

        const sponsorLink = "{{direct_link}}";
        const userId = "{{user_id}}";
        
        // Use localStorage so progress isn't lost if they accidentally close the app early
        let currentStep = parseInt(localStorage.getItem('ad_steps_' + userId) || '0');
        const totalSteps = 4;

        const btn = document.getElementById("actionBtn");
        const progressFill = document.getElementById("progressFill");
        const stepCounter = document.getElementById("stepCounter");
        const successMsg = document.getElementById("successMsg");

        // Initialize UI based on saved progress
        updateUI();
        if (currentStep >= totalSteps) {
            showSuccess();
        }

        function handleVisit() {
            if (!userId) return tg.showAlert("Error: User ID missing.");

            // 1. Open the sponsor link safely inside Telegram
            tg.openLink(sponsorLink);

            // 2. Increment and Save Step
            currentStep++;
            localStorage.setItem('ad_steps_' + userId, currentStep);
            updateUI();

            // 3. Logic handling
            if (currentStep >= totalSteps) {
                btn.disabled = true;
                btn.innerHTML = "⌛ Verifying...";
                unlockUser();
            } else {
                // Temporary "wait" state to prevent fast-clicking
                btn.disabled = true;
                let timeLeft = 5;
                btn.innerHTML = `⏳ Wait ${timeLeft}s...`;
                
                let timer = setInterval(() => {
                    timeLeft--;
                    btn.innerHTML = `⏳ Wait ${timeLeft}s...`;
                    if (timeLeft <= 0) {
                        clearInterval(timer);
                        btn.disabled = false;
                        btn.innerHTML = `🚀 VISIT SPONSOR (Step ${currentStep + 1})`;
                    }
                }, 1000);
            }
        }

        function updateUI() {
            const percent = (currentStep / totalSteps) * 100;
            progressFill.style.width = percent + "%";
            stepCounter.innerHTML = `Steps Completed: ${currentStep} / ${totalSteps}`;
        }

        function showSuccess() {
            btn.style.display = "none";
            successMsg.style.display = "block";
            stepCounter.innerText = "✅ Verification Complete!";
            
            tg.MainButton.setText("RETURN TO BOT");
            tg.MainButton.show();
            tg.MainButton.onClick(() => tg.close());
        }

        function unlockUser() {
            // This calls your RENDER bot's API, not Netlify!
            fetch(`/api/grant/${userId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success") {
                        localStorage.setItem('ad_steps_' + userId, '0'); // Reset for next time
                        showSuccess();
                    } else {
                        throw new Error("Server rejected unlock");
                    }
                })
                .catch(err => {
                    tg.showAlert("Server error. Please try again.");
                    btn.disabled = false;
                    btn.innerHTML = "🔄 RETRY UNLOCK";
                });
        }
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
