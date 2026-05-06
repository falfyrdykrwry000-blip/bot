import os
import requests
from flask import Flask, request

app = Flask(__name__)

# إعدادات البوت
TOKEN = "8490776623:AAFD3Q6th51Y_DDkx0OEj-gVP7U5rpc3HO8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# إعدادات خادم الذكاء الاصطناعي
AI_SERVER = "https://kruri.qzz.io/chat/send"

def get_ai_reply(user_message):
    """إرسال الرسالة لخادم الذكاء الاصطناعي واستقبال الرد"""
    try:
        response = requests.post(
            AI_SERVER,
            json={
                "message": f"أجب باللغة العربية فقط: {user_message}",
                "model": "llama-3.3-70b-versatile"
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        data = response.json()
        return data.get("reply", "عذراً، لم أستطع الرد حالياً")
    except Exception as e:
        return f"خطأ في الاتصال بالذكاء الاصطناعي"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        # إرسال حالة "يكتب..."
        requests.post(f"{BASE_URL}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing"
        })
        
        # الحصول على رد الذكاء الاصطناعي
        reply = get_ai_reply(text)
        
        # إرسال الرد
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply
        })
    
    return "OK", 200

@app.route("/")
def home():
    return "Bot AI is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)