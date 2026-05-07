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

def send_message(chat_id, text, reply_markup=None):
    """إرسال رسالة نصية مع أزرار اختيارية"""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

def get_main_keyboard():
    """الأزرار الرئيسية للبوت"""
    return {
        "keyboard": [
            [{"text": "💬 محادثة عادية"}, {"text": "🖼️ إنشاء صورة"}],
            [{"text": "ℹ️ عن البوت"}, {"text": "🔄 إعادة تشغيل"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def get_back_keyboard():
    """زر الرجوع"""
    return {
        "keyboard": [[{"text": "🔙 رجوع للقائمة"}]],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

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
        
        # 🎯 التعامل مع الأوامر والأزرار
        if text == "/start" or text == "🔄 إعادة تشغيل":
            send_message(
                chat_id,
                "👋 <b>مرحباً بك في بوت FM AI!</b>\n\n"
                "أنا بوت ذكي مدعوم بالذكاء الاصطناعي، أقدر أساعدك في:\n"
                "• 💬 محادثة ذكية بالعربية\n"
                "• 🖼️ إنشاء صور بالوصف\n\n"
                "اختر من الأزرار أدناه 👇",
                get_main_keyboard()
            )
        
        elif text == "ℹ️ عن البوت":
            send_message(
                chat_id,
                "🤖 <b>بوت FM AI</b>\n\n"
                "• النسخة: 1.0\n"
                "• الذكاء: Llama 3.3 70B\n"
                "• الخادم: kruri.qzz.io\n"
                "• المطور: مريم محمد 🛡️\n\n"
                "شكراً لاستخدامك البوت! ❤️",
                get_main_keyboard()
            )
        
        elif text == "🔙 رجوع للقائمة":
            send_message(chat_id, "تم الرجوع للقائمة الرئيسية ✅", get_main_keyboard())
        
        elif text == "💬 محادثة عادية":
            send_message(chat_id, "تم تفعيل وضع المحادثة 💬\nاكتب رسالتك وسأرد عليك فوراً!", get_back_keyboard())
        
        elif text == "🖼️ إنشاء صورة":
            send_message(chat_id, "تم تفعيل وضع إنشاء الصور 🖼️\nاكتب وصف الصورة وسأحاول إنشائها!", get_back_keyboard())
        
        else:
            # إرسال للذكاء الاصطناعي
            reply = get_ai_reply(text)
            send_message(chat_id, reply, get_back_keyboard())
    
    return "OK", 200

@app.route("/")
def home():
    return "Bot AI is running with Keyboards", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)