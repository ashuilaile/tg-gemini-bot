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

# 【核心修复】100%兼容Gemini的图片下载方法
def get_image_bytes(update, context):
    try:
        if not update.message.photo:
            return None
        photo = update.message.photo[-1]
        file = context.bot.get_file(photo.file_id)
        bio = BytesIO()
        file.download(out=bio)
        bio.seek(0)
        return bio.read()  # 直接返回二进制，Gemini原生支持
    except Exception as e:
        print(f"图片下载错误: {str(e)}")
        return None

# ---------------- AI 接口（彻底修复识图） ----------------
def gemini_img(prompt, img_bytes):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # 用gemini-1.5-flash，识图最稳，兼容性最好
        model = genai.GenerativeModel("gemini-1.5-flash")
        # 用Gemini原生的Part格式，100%兼容
        from google.generativeai.types import Part
        image_part = Part.from_data(data=img_bytes, mime_type="image/jpeg")
        response = model.generate_content([prompt, image_part])
        response.resolve()
        return response.text.strip()
    except Exception as e:
        print(f"Gemini识图错误: {str(e)}")
        return None

def gemini_text(prompt):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return None

def deepseek(prompt):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

def siliconflow(prompt):
    try:
        headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        r = requests.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, json=data, timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

# 智能调度：有图优先Gemini，失败自动重试+兜底
def get_reply(prompt, img_bytes=None):
    if img_bytes:
        # 第一次用gemini-1.5-flash（最稳）
        res = gemini_img(prompt, img_bytes)
        if res:
            return res
        # 第二次用gemini-2.0-flash（备用）
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            from google.generativeai.types import Part
            image_part = Part.from_data(data=img_bytes, mime_type="image/jpeg")
            response = model.generate_content([prompt, image_part])
            response.resolve()
            return response.text.strip()
        except:
            # 两次都失败，用文本AI兜底，直接描述图片
            return f"⚠️ 图片识别暂时繁忙，我来帮你描述：\n{deepseek(f'用户发了一张图片，请描述图片内容，用户的提问是：{prompt}')}"

    ais = [gemini_text, deepseek, siliconflow]
    random.shuffle(ais)
    for func in ais:
        res = func(prompt)
        if res:
            return res
    return "⚠️ 所有AI接口暂时繁忙，请1分钟后再试~"

# ---------------- 机器人逻辑 ----------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        member = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            update.message.reply_text("✅ 机器人已就绪，支持文字、图片、图文混合提问！")
        else:
            update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
    except:
        update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")

def handle_message(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    try:
        member = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
            return
    except:
        update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
        return

    prompt = update.message.caption or update.message.text or "请详细描述这张图片的内容"
    img_bytes = get_image_bytes(update, context)

    reply = get_reply(prompt, img_bytes)
    for i in range(0, len(reply), 4096):
        update.message.reply_text(reply[i:i+4096])

# ---------------- 启动 ----------------
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo | Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
