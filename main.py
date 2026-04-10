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

# 安全下载图片
def get_image_bytes(update, context):
    try:
        if not update.message.photo:
            return None
        photo = update.message.photo[-1]
        file = context.bot.get_file(photo.file_id)
        bio = BytesIO()
        file.download(out=bio)
        bio.seek(0)
        return bio
    except Exception as e:
        print("图片下载错误:", e)
        return None

# ---------------- AI 接口 ----------------
def gemini_img(prompt, img_bytes):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        res = model.generate_content([prompt, img_bytes])
        return res.text.strip()
    except:
        return None

def gemini_text(prompt):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        res = model.generate_content(prompt)
        return res.text.strip()
    except:
        return None

def deepseek(prompt):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return None

def siliconflow(prompt):
    try:
        headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}"}
        data = {"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": prompt}]}
        r = requests.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, json=data)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return None

# 智能调度
def reply(prompt, img=None):
    if img:
        res = gemini_img(prompt, img)
        if res: return res
        return "❌ 图片识别暂时不可用"

    for f in [gemini_text, deepseek, siliconflow]:
        res = f(prompt)
        if res: return res
    return "⚠️ 繁忙，请稍后再试"

# ---------------- 机器人逻辑 ----------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("✅ 机器人已启动，支持文字、图片、图文")

def msg(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    try:
        m = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if m.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")
            return
    except:
        update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")
        return

    prompt = update.message.caption or update.message.text or "描述图片"
    img = get_image_bytes(update, context)
    update.message.reply_text(reply(prompt, img))

# ---------------- 启动 ----------------
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    d = updater.dispatcher
    d.add_handler(CommandHandler("start", start))
    d.add_handler(MessageHandler(Filters.photo | Filters.text, msg))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
