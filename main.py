import os
import random
import requests
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# ===================== 环境变量 =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")
GROUP_LINK = "https://t.me/HWJLJL"
# ====================================================

# 【修复核心】优化图片下载+格式转换，完美适配Gemini
def get_image_bytes(update, context):
    try:
        if not update.message.photo:
            return None
        # 取最高清的图片
        photo = update.message.photo[-1]
        file = context.bot.get_file(photo.file_id)
        bio = BytesIO()
        file.download(out=bio)
        bio.seek(0)
        # 转成Gemini要求的PIL Image格式
        img = Image.open(bio)
        return img
    except Exception as e:
        print(f"图片处理错误: {str(e)}")
        return None

# ---------------- AI 接口（彻底修复Gemini识图） ----------------
def gemini_img(prompt, img):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # 用gemini-2.0-flash，识图能力更强
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content([prompt, img])
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

# 智能调度：有图优先Gemini，无图轮询三AI
def get_reply(prompt, img=None):
    if img:
        res = gemini_img(prompt, img)
        if res:
            return res
        # 识图失败，降级用文本AI兜底
        return "⚠️ 图片识别暂时繁忙，已为您切换文本回复：\n" + get_reply(prompt, None)

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
    # 只处理私聊
    if update.effective_chat.type != "private":
        return

    # 验证群成员
    user_id = update.effective_user.id
    try:
        member = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
            return
    except:
        update.message.reply_text(f"❌ 请先加入群组后再使用机器人！\n群链接：{GROUP_LINK}")
        return

    # 提取提问内容
    prompt = update.message.caption or update.message.text or "请详细描述这张图片的内容"
    # 提取图片
    img = get_image_bytes(update, context)

    # 获取回复
    reply = get_reply(prompt, img)
    # 自动拆分长消息，避免Telegram发送失败
    for i in range(0, len(reply), 4096):
        update.message.reply_text(reply[i:i+4096])

# ---------------- 启动 ----------------
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    # 同时监听图片和文本消息
    dp.add_handler(MessageHandler(Filters.photo | Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
