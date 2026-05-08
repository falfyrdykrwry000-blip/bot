import os
import requests
import json
from flask import Flask, request

app = Flask(__name__)

# إعدادات البوت
TOKEN = "8490776623:AAFD3Q6th51Y_DDkx0OEj-gVP7U5rpc3HO8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ============ ✅ إعدادات خادم الذكاء الاصطناعي (مُحدثة) ============
AI_SERVER = "https://kruri.qzz.io/api/chat"
API_KEY = "fm-84a32c9850954ac995cbd6f5"

def get_ai_reply(user_message):
    """إرسال الرسالة لخادم الذكاء الاصطناعي واستقبال الرد"""
    try:
        # ✅ تنسيق JSON متوافق مع الخادم الجديد
        payload = {
            "messages": [
                {"role": "user", "content": f"أجب باللغة العربية فقط: {user_message}"}
            ],
            "model": "balanced",
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        response = requests.post(
            AI_SERVER,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY  # ✅ إضافة مفتاح API
            },
            timeout=60
        )
        
        data = response.json()
        
        # ✅ استخراج الرد من التنسيقات المختلفة
        if response.status_code == 200:
            # تنسيق OpenAI compatible
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            # تنسيق reply المباشر
            elif "reply" in data:
                return data["reply"]
            else:
                return "عذراً، لم أستطع معالجة الرد"
        else:
            error_msg = data.get("error", "خطأ غير معروف")
            return f"⚠️ خطأ من الخادم: {error_msg}"
            
    except requests.exceptions.Timeout:
        return "⏱️ انتهت مهلة الاتصال بالخادم. حاول مرة أخرى."
    except requests.exceptions.ConnectionError:
        return "❌ لا يمكن الاتصال بالخادم. تأكد من تشغيله."
    except Exception as e:
        return f"❌ خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"

def send_message(chat_id, text, reply_markup=None):
    """إرسال رسالة نصية مع أزرار اختيارية"""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    response = requests.post(f"{BASE_URL}/sendMessage", json=payload)
    return response.json().get("result", {}).get("message_id")

def edit_message(chat_id, message_id, text, reply_markup=None):
    """تعديل رسالة موجودة"""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    requests.post(f"{BASE_URL}/editMessageText", json=payload)

def get_main_keyboard():
    """الأزرار الرئيسية للبوت"""
    return {
        "inline_keyboard": [
            [{"text": "💬 محادثة عادية", "callback_data": "chat_mode"}],
            [{"text": "🚀 ابدأ الآن مجاناً", "url": "https://kruri.qzz.io"}],
            [{"text": "ℹ️ عن البوت", "callback_data": "about"}],
            [{"text": "🔄 إعادة تشغيل", "callback_data": "restart"}]
        ]
    }

def get_back_keyboard():
    """زر الرجوع"""
    return {
        "inline_keyboard": [
            [{"text": "🔙 رجوع للقائمة", "callback_data": "back_to_menu"}]
        ]
    }

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    
    # ✅ معالجة الرسائل النصية
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        user_name = data["message"]["from"].get("first_name", "مستخدم")
        
        # إرسال حالة "يكتب..."
        requests.post(f"{BASE_URL}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing"
        })
        
        if text == "/start":
            send_message(
                chat_id,
                f"👋 <b>مرحباً {user_name} في بوت FM AI!</b>\n\n"
                "أنا بوت ذكي مدعوم بالذكاء الاصطناعي، أقدر أساعدك في:\n"
                "• 💬 محادثة ذكية بالعربية\n"
                "• 📝 الإجابة على أسئلتك\n"
                "• 🧠 تقديم معلومات مفيدة\n"
                "• 🌐 الوصول للموقع: kruri.qzz.io\n\n"
                "اختر من الأزرار أدناه 👇",
                get_main_keyboard()
            )
        elif text == "/help":
            send_message(
                chat_id,
                "📚 <b>كيفية استخدام البوت:</b>\n\n"
                "• اكتب سؤالك مباشرة\n"
                "• اضغط على الأزرار للتنقل\n"
                "• استخدم /start للعودة للقائمة\n\n"
                "البوت يستخدم نموذج Llama 3.3 70B",
                get_back_keyboard()
            )
        else:
            # ✅ إرسال للذكاء الاصطناعي
            reply = get_ai_reply(text)
            send_message(chat_id, reply, get_back_keyboard())
    
    # ✅ معالجة الأزرار (callback queries)
    elif data and "callback_query" in data:
        callback_id = data["callback_query"]["id"]
        message = data["callback_query"]["message"]
        chat_id = message["chat"]["id"]
        message_id = message["message_id"]
        callback_data = data["callback_query"]["data"]
        
        # الرد على callback query
        requests.post(f"{BASE_URL}/answerCallbackQuery", json={
            "callback_query_id": callback_id,
            "text": "✅ تم"
        })
        
        if callback_data == "restart":
            edit_message(
                chat_id, message_id,
                "👋 <b>تم إعادة التشغيل!</b>\n\nاختر من الأزرار أدناه 👇",
                get_main_keyboard()
            )
        
        elif callback_data == "about":
            edit_message(
                chat_id, message_id,
                "🤖 <b>بوت FM AI</b>\n\n"
                "• النسخة: 2.0\n"
                "• الذكاء: Llama 3.3 70B\n"
                "• الخادم: kruri.qzz.io\n"
                "• API: متوافق مع OpenAI\n"
                "• المطور: فريق FM AI\n\n"
                "🚀 <a href='https://kruri.qzz.io'>زيارة الموقع الرسمي</a>",
                get_main_keyboard()
            )
        
        elif callback_data == "chat_mode":
            edit_message(
                chat_id, message_id,
                "💬 <b>تم تفعيل وضع المحادثة</b>\n\n"
                "اكتب رسالتك وسأرد عليك فوراً!\n"
                "يمكنك سؤالي عن أي شيء تريده.",
                get_back_keyboard()
            )
        
        elif callback_data == "back_to_menu":
            edit_message(
                chat_id, message_id,
                "👋 <b>القائمة الرئيسية</b>\n\nاختر من الأزرار أدناه 👇",
                get_main_keyboard()
            )
    
    return "OK", 200

@app.route("/")
def home():
    return """
    <h1>🤖 بوت FM AI يعمل بنجاح</h1>
    <p>الخادم: kruri.qzz.io</p>
    <p>API: /api/chat</p>
    """, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)