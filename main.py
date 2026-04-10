import os
import random
import requests
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import google.generativeai as genai

# ===================== 【环境变量】全部从这里读取 =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")
GROUP_LINK = "https://t.me/HWJLJL"
# ====================================================================

# 1. Gemini
def ask_gemini(prompt):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        res = model.generate_content(prompt)
        return res.text.strip()
    except:
        return None

# 2. DeepSeek
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

# 3. 硅基流动
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
            "temperature": 0.7,
            "max_tokens": 1024
        }
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

# 自动轮询可用 AI
def get_ai_reply(prompt):
    ais = [ask_gemini, ask_deepseek, ask_siliconflow]
    random.shuffle(ais)

    for func in ais:
        reply = func(prompt)
        if reply:
            return reply

    return "⚠️ 机器人繁忙，请1分钟后再试~"

# ===================== 机器人逻辑 =====================
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status in ["member", "administrator", "creator"]:
            update.message.reply_text("✅ 机器人已启动，直接发消息即可对话！")
        else:
            update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
    except:
        update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")

def reply_message(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
            return
    except:
        update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
        return

    text = update.message.text
    if not text:
        return

    reply = get_ai_reply(text)
    update.message.reply_text(reply)

# 启动
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
