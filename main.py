import os
import random
import requests
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ===================== 环境变量（无OCR） =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")
GROUP_LINK = "https://t.me/HWJLJL"
# ============================================================

# ---------------------- AI 接口（纯文字） ----------------------
def ask_gemini(prompt):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        return model.generate_content(prompt).text.strip()
    except Exception as e:
        print(f"Gemini Error: {str(e)}")
        return None

def ask_deepseek(prompt):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"DeepSeek Error: {str(e)}")
        return None

def ask_siliconflow(prompt):
    try:
        headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        r = requests.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, json=data, timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"SiliconFlow Error: {str(e)}")
        return None

def get_ai_reply(prompt):
    ais = [ask_gemini, ask_deepseek, ask_siliconflow]
    random.shuffle(ais)
    for func in ais:
        res = func(prompt)
        if res:
            return res
    return "⚠️ 所有接口繁忙，请稍后再试~"

# ---------------------- 机器人逻辑 ----------------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status in ["member", "administrator", "creator"]:
            update.message.reply_text("✅ 机器人已启动！发送文字即可对话")
        else:
            update.message.reply_text(f"❌ 请先加入群组再使用\n{GROUP_LINK}")
    except Exception as e:
        print(f"Start Error: {str(e)}")
        update.message.reply_text(f"❌ 请先加入群组再使用\n{GROUP_LINK}")

def reply_message(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"❌ 请先加入群组再使用\n{GROUP_LINK}")
            return
    except Exception as e:
        print(f"Auth Error: {str(e)}")
        update.message.reply_text(f"❌ 请先加入群组再使用\n{GROUP_LINK}")
        return

    # 收到图片直接提示
    if update.message.photo:
        update.message.reply_text("🖼️ 图片功能暂未开放，仅支持文字对话~")
        return

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
