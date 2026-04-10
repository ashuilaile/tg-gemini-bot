import os
import random
import requests
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import google.generativeai as genai
from io import BytesIO

# ===================== 环境变量 =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")
GROUP_LINK = "https://t.me/HWJLJL"
# ====================================================

# 下载 Telegram 图片
def download_image(file_obj, bot):
    try:
        file = bot.get_file(file_obj.file_id)
        img_bytes = BytesIO()
        file.download(out=img_bytes)
        img_bytes.seek(0)
        return img_bytes
    except:
        return None

# 1. Gemini（支持图片）
def ask_gemini(prompt, img_bytes=None):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        if img_bytes:
            response = model.generate_content([prompt, img_bytes])
        else:
            response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return None

# 2. DeepSeek（纯文本）
def ask_deepseek(prompt):
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

# 3. 硅基流动（纯文本）
def ask_siliconflow(prompt):
    try:
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

# 智能回复：有图走Gemini，无图轮询
def get_ai_reply(prompt, img_bytes=None):
    if img_bytes:
        return ask_gemini(prompt, img_bytes)
    
    ais = [ask_gemini, ask_deepseek, ask_siliconflow]
    random.shuffle(ais)
    for func in ais:
        reply = func(prompt)
        if reply:
            return reply
    return "⚠️ 繁忙，请稍后再试"

# ===================== 机器人逻辑 =====================
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status in ["member", "administrator", "creator"]:
            update.message.reply_text("✅ 机器人已启动，可发文字/图片/图文")
        else:
            update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")
    except:
        update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")

def handle_message(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")
            return
    except:
        update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")
        return

    prompt = update.message.caption or update.message.text or "描述这张图片"
    img_bytes = None

    if update.message.photo:
        img_file = update.message.photo[-1]
        img_bytes = download_image(img_file, context.bot)
        if not img_bytes:
            update.message.reply_text("❌ 图片下载失败")
            return

    reply = get_ai_reply(prompt, img_bytes)
    update.message.reply_text(reply)

# ======================================================

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
