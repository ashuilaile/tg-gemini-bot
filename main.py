import os
import random
import requests
import telegram
from telegram import Update, File
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from io import BytesIO

# ===================== 【全部环境变量】 =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY")  # <-- 你新注册的OCR放这里
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")
GROUP_LINK = "https://t.me/HWJLJL"
# ============================================================

# ---------------------- 免费 OCR 图片识别 ----------------------
def ocr_image(image_bytes: bytes) -> str:
    try:
        url = "https://api.ocr.space/parse/image"
        data = {
            "apikey": OCR_SPACE_API_KEY,
            "language": "chs",  # 简体中文
            "isOverlayRequired": False
        }
        files = {
            "file": ("image.jpg", image_bytes, "image/jpeg")
        }
        res = requests.post(url, data=data, files=files, timeout=15)
        data = res.json()

        if not data.get("IsErrored", True):
            return data["ParsedResults"][0]["ParsedText"].strip()
        return "❌ 无法识别图片文字"
    except:
        return "❌ 图片识别失败"

# ---------------------- AI 接口 ----------------------
def ask_gemini(prompt):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        return model.generate_content(prompt).text.strip()
    except:
        return None

def ask_deepseek(prompt):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

def ask_siliconflow(prompt):
    try:
        headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}"}
        data = {"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": prompt}]}
        r = requests.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, json=data)
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

# 自动轮询可用AI
def get_ai_reply(prompt):
    ais = [ask_gemini, ask_deepseek, ask_siliconflow]
    random.shuffle(ais)
    for func in ais:
        res = func(prompt)
        if res:
            return res
    return "⚠️ 机器人繁忙，请稍后再试~"

# ---------------------- 机器人逻辑 ----------------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status in ["member", "administrator", "creator"]:
            update.message.reply_text("✅ 机器人已启动！支持文字 + 图片")
        else:
            update.message.reply_text(f"❌ 请先加群再使用\n{GROUP_LINK}")
    except:
        update.message.reply_text(f"❌ 请先加群再使用\n{GROUP_LINK}")

def reply_message(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"❌ 请先加群再使用\n{GROUP_LINK}")
            return
    except:
        update.message.reply_text(f"❌ 请先加群再使用\n{GROUP_LINK}")
        return

    # ---------------------- 处理图片 ----------------------
    if update.message.photo:
        photo = update.message.photo[-1]
        file: File = context.bot.get_file(photo.file_id)
        bio = BytesIO()
        file.download(out=bio)
        bio.seek(0)
        
        # OCR识别
        img_text = ocr_image(bio.read())
        user_prompt = update.message.caption or "请解析这段图片文字"
        full_prompt = f"图片文字内容：{img_text}\n用户需求：{user_prompt}"
        
        ai_reply = get_ai_reply(full_prompt)
        update.message.reply_text(f"🖼️ OCR识别结果：\n{img_text}\n\n🤖 AI回复：\n{ai_reply}")
        return

    # ---------------------- 处理文字 ----------------------
    text = update.message.text
    if not text:
        return
    update.message.reply_text(get_ai_reply(text))

# ---------------------- 启动 ----------------------
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.all & ~Filters.command, reply_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
