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
    """الأزرار الرئيسية الشفافة للبوت"""
    return {
        "inline_keyboard": [
            [{"text": "💬 محادثة عادية", "callback_data": "chat_mode"}],
            [{"text": "ℹ️ عن البوت", "callback_data": "about"}],
            [{"text": "🔄 إعادة تشغيل", "callback_data": "restart"}]
        ]
    }

def get_back_keyboard():
    """زر الرجوع الشفاف"""
    return {
        "inline_keyboard": [
            [{"text": "🔙 رجوع للقائمة", "callback_data": "back_to_menu"}]
        ]
    }

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    
    # معالجة الرسائل النصية
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        # إرسال حالة "يكتب..."
        requests.post(f"{BASE_URL}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing"
        })
        
        # التعامل مع الأوامر
        if text == "/start":
            send_message(
                chat_id,
                "👋 <b>مرحباً بك في بوت FM AI!</b>\n\n"
                "أنا بوت ذكي مدعوم بالذكاء الاصطناعي، أقدر أساعدك في:\n"
                "• 💬 محادثة ذكية بالعربية\n"
                "• 📝 الإجابة على أسئلتك\n"
                "• 🧠 تقديم معلومات مفيدة\n\n"
                "اختر من الأزرار أدناه 👇",
                get_main_keyboard()
            )
        else:
            # إرسال للذكاء الاصطناعي
            reply = get_ai_reply(text)
            send_message(chat_id, reply, get_main_keyboard())
    
    # معالجة الأزرار الشفافة (callback queries)
    elif data and "callback_query" in data:
        callback_id = data["callback_query"]["id"]
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        callback_data = data["callback_query"]["data"]
        
        # الرد على callback query
        requests.post(f"{BASE_URL}/answerCallbackQuery", json={
            "callback_query_id": callback_id
        })
        
        # إرسال حالة "يكتب..."
        requests.post(f"{BASE_URL}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing"
        })
        
        if callback_data == "restart":
            send_message(
                chat_id,
                "👋 <b>مرحباً بك في بوت FM AI!</b>\n\n"
                "أنا بوت ذكي مدعوم بالذكاء الاصطناعي، أقدر أساعدك في:\n"
                "• 💬 محادثة ذكية بالعربية\n"
                "• 📝 الإجابة على أسئلتك\n"
                "• 🧠 تقديم معلومات مفيدة\n\n"
                "اختر من الأزرار أدناه 👇",
                get_main_keyboard()
            )
        
        elif callback_data == "about":
            send_message(
                chat_id,
                "🤖 <b>بوت FM AI</b>\n\n"
                "• النسخة: 2.0\n"
                "• الذكاء: Llama 3.3 70B\n"
                "• الخادم: kruri.qzz.io\n"
                "• المطور: مريم محمد 🛡️\n\n"
                "شكراً لاستخدامك البوت! ❤️",
                get_main_keyboard()
            )
        
        elif callback_data == "chat_mode":
            send_message(
                chat_id,
                "💬 <b>تم تفعيل وضع المحادثة</b>\n\n"
                "اكتب رسالتك وسأرد عليك فوراً!\n"
                "يمكنك سؤالي عن أي شيء تريده.",
                get_main_keyboard()
            )
        
        elif callback_data == "back_to_menu":
            send_message(
                chat_id,
                "✅ <b>تم الرجوع للقائمة الرئيسية</b>\n\n"
                "اختر ما تريد من الأزرار أدناه:",
                get_main_keyboard()
            )
    
    return "OK", 200

@app.route("/")
def home():
    return "Bot AI is running with Inline Keyboards", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)