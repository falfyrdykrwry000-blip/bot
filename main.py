import os
from flask import Flask, request

app = Flask(name)

TOKEN = "8490776623:AAFD3Q6th51Y_DDkx0OEj-gVP7U5rpc3HO8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        # إرسال رد بسيط
        import requests
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"مرحباً! أنت قلت: {text}"
        })
    return "OK", 200

@app.route("/")
def home():
    return "Bot is running", 200

if name == "main":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)