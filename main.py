import os
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import google.generativeai as genai

# 读取环境变量
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")

# 配置 Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# /start 命令
def start(update: Update, context: CallbackContext):
    update.message.reply_text("✅ 机器人已启动，直接发消息即可对话！")

# 消息处理
def reply_message(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    if chat_id != REQUIRED_GROUP_ID:
        return

    user_text = update.message.text
    if not user_text:
        return

    try:
        response = model.generate_content(user_text)
        reply = response.text
    except Exception as e:
        reply = f"❌ 出错：{str(e)}"

    update.message.reply_text(reply)

# 启动机器人
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
