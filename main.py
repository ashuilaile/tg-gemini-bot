import os
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import google.generativeai as genai

# ===================== 配置区域 =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")

# 这里填写你的群链接（自己修改）
GROUP_LINK = "https://t.me/hwjljl"

# ===================================================

# 配置 Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# /start 命令
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        member = context.bot.get_chat_member(chat_id=REQUIRED_GROUP_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            update.message.reply_text("✅ 机器人已启动，直接发消息即可对话！")
        else:
            # 没加群 → 提示+群链接
            update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
    except:
        update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")

# 消息处理
def reply_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # 只允许私聊
    if chat_type != "private":
        return

    try:
        # 检查是否在群里
        member = context.bot.get_chat_member(chat_id=REQUIRED_GROUP_ID, user_id=user_id)
        if member.status not in ["member", "administrator", "creator"]:
            # 没加群 → 回复提示
            update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
            return
    except:
        # 异常也按未加群处理
        update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
        return

    # 正常对话
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
