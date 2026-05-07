import os
import requests
import random
import json
from flask import Flask, request

app = Flask(__name__)

# إعدادات تطبيق Telegram (MTProto)
API_ID = 26938834
API_HASH = "2b04792eff86cad6ba50ca001920fb7d"

# إعدادات البوت
TOKEN = "8490776623:AAFD3Q6th51Y_DDkx0OEj-gVP7U5rpc3HO8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# إعدادات خادم الذكاء الاصطناعي
AI_SERVER = "https://kruri.qzz.io/chat/send"

# تخزين مؤقت للمستخدمين
users = {}

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

def request_phone_keyboard():
    return {
        "keyboard": [[{"text": "📱 مشاركة رقم الهاتف", "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "💬 محادثة عادية"}, {"text": "🖼️ إنشاء صورة"}],
            [{"text": "ℹ️ عن البوت"}, {"text": "🔄 إعادة تشغيل"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def generate_verification_code():
    return str(random.randint(100000, 999999))

def get_ai_reply(user_message):
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
    except:
        return "خطأ في الاتصال بالذكاء الاصطناعي"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    
    if not data or "message" not in data:
        return "OK", 200
    
    chat_id = data["message"]["chat"]["id"]
    user = users.get(chat_id, {"verified": False, "phone": None, "code": None})
    
    # ✅ مشاركة جهة الاتصال
    if "contact" in data["message"]:
        phone = data["message"]["contact"]["phone_number"]
        code = generate_verification_code()
        
        users[chat_id] = {
            "verified": False,
            "phone": phone,
            "code": code,
            "attempts": 0
        }
        
        send_message(
            chat_id,
            f"✅ تم استلام رقم هاتفك: <code>{phone}</code>\n\n"
            f"🔐 <b>رمز التحقق الخاص بك هو:</b>\n<code>{code}</code>\n\n"
            "📝 <b>الرجاء إرسال هذا الرمز للتأكيد</b>",
            {"remove_keyboard": True}
        )
        return "OK", 200
    
    text = data["message"].get("text", "")
    
    # ✅ مستخدم غير موثق
    if not user.get("verified"):
        if text == "/start" or text == "🔄 إعادة تشغيل":
            users[chat_id] = {"verified": False, "phone": None, "code": None, "attempts": 0}
            send_message(
                chat_id,
                "👋 <b>مرحباً بك في بوت FM AI!</b>\n\n"
                "للاستمرار، يجب التحقق من هويتك.\n"
                "الرجاء مشاركة رقم هاتفك للمتابعة 👇",
                request_phone_keyboard()
            )
        
        elif user.get("code") and text == user["code"]:
            users[chat_id]["verified"] = True
            send_message(
                chat_id,
                "✅ <b>تم التحقق بنجاح!</b>\n\n"
                "🎉 أهلاً بك في بوت FM AI!\n"
                "اختر من الأزرار أدناه للبدء 👇",
                get_main_keyboard()
            )
        
        elif user.get("code"):
            users[chat_id]["attempts"] += 1
            if users[chat_id]["attempts"] >= 3:
                users[chat_id] = {"verified": False, "phone": None, "code": None, "attempts": 0}
                send_message(
                    chat_id,
                    "❌ <b>تم تجاوز عدد المحاولات!</b>\n\n"
                    "الرجاء إعادة تشغيل البوت /start",
                    {"remove_keyboard": True}
                )
            else:
                send_message(
                    chat_id,
                    f"❌ <b>رمز التحقق غير صحيح!</b>\n"
                    f"لديك {3 - users[chat_id]['attempts']} محاولات متبقية."
                )
        
        return "OK", 200
    
    # ✅ مستخدم موثق
    requests.post(f"{BASE_URL}/sendChatAction", json={
        "chat_id": chat_id, "action": "typing"
    })
    
    if text == "/start" or text == "🔄 إعادة تشغيل":
        send_message(
            chat_id,
            "👋 <b>مرحباً بك في بوت FM AI!</b>\n\n"
            f"• معرف التطبيق: <code>{API_ID}</code>\n"
            "• الذكاء: Llama 3.3 70B\n"
            "• المطور: مريم محمد 🛡️\n\n"
            "اختر من الأزرار أدناه 👇",
            get_main_keyboard()
        )
    
    elif text == "ℹ️ عن البوت":
        send_message(
            chat_id,
            "🤖 <b>بوت FM AI</b>\n\n"
            f"• رقم الهاتف: <code>{user['phone']}</code>\n"
            f"• معرف التطبيق: <code>{API_ID}</code>\n"
            f"• اسم التطبيق: <code>krory.iq</code>\n"
            f"• الاسم المختصر: <code>KRARAPP</code>\n"
            "• النسخة: 1.0\n"
            "• الذكاء: Llama 3.3 70B\n"
            "• المطور: مريم محمد 🛡️",
            get_main_keyboard()
        )
    
    elif text == "💬 محادثة عادية":
        send_message(chat_id, "تم تفعيل وضع المحادثة 💬\nاكتب رسالتك!", get_main_keyboard())
    
    elif text == "🖼️ إنشاء صورة":
        send_message(chat_id, "تم تفعيل وضع إنشاء الصور 🖼️\nاكتب وصف الصورة!", get_main_keyboard())
    
    else:
        reply = get_ai_reply(text)
        send_message(chat_id, reply, get_main_keyboard())
    
    return "OK", 200

@app.route("/")
def home():
    return json.dumps({
        "app": "FM AI Bot",
        "api_id": API_ID,
        "app_title": "krory.iq",
        "app_short_name": "KRARAPP",
        "status": "running"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)