import os
import time
import random
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import google.generativeai as genai

# 从环境变量读取配置，安全不泄露
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
REQUIRED_GROUP_ID = int(os.environ.get("REQUIRED_GROUP_ID", 0))

genai.configure(api_key=GEMINI_API_KEY)

user_time = {}
captcha_pending = {}

# 群组权限校验
async def is_group_member(context, user_id):
    if REQUIRED_GROUP_ID == 0:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_GROUP_ID, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        print(f"群组校验失败: {e}")
        return False

# 启动命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_group_member(context, user_id):
        await update.message.reply_text("❌ 你不在授权群组，无法使用机器人")
        return
    await update.message.reply_text("✅ 机器人已启动，直接发消息聊天~")

# 聊天处理
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    # 先校验群组权限
    if not await is_group_member(context, uid):
        await update.message.reply_text("❌ 你不在授权群组，无法使用机器人")
        return

    # 验证码验证
    if uid in captcha_pending:
        if text == captcha_pending[uid]:
            del captcha_pending[uid]
            user_time[uid] = []
            await update.message.reply_text("✅ 验证通过！")
        else:
            code = str(random.randint(1000, 9999))
            captcha_pending[uid] = code
            await update.message.reply_text(f"❌ 验证码错误，请输入：{code}")
        return

    # 频率限制
    now = time.time()
    ts = [t for t in user_time.get(uid, []) if now - t < 10]
    ts.append(now)
    user_time[uid] = ts
    if len(ts) > 3:
        code = str(random.randint(1000, 9999))
        captcha_pending[uid] = code
        await update.message.reply_text(f"⚠️ 发送过快，请输入验证码：{code}")
        return

    # AI回复
    msg = await update.message.reply_text("⏳ 正在思考中...")
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        res = model.generate_content(text)
        await msg.edit_text(res.text[:4000])
    except Exception as e:
        print(f"AI调用失败: {e}")
        await msg.edit_text("❌ 服务暂时出错，请稍后重试")

# 启动机器人
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("✅ 机器人运行中，24小时在线...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
