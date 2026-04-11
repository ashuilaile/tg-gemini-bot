import os
import random
import requests
import telegram
from telegram import Update, File
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from io import BytesIO

# ===================== 环境变量（OCR加默认值） =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "")  # 加默认值，解决构建报错
REQUIRED_GROUP_ID = os.getenv("REQUIRED_GROUP_ID")
GROUP_LINK = "https://t.me/HWJLJL"
# ====================================================================

# ---------------------- OCR 图片识别 ----------------------
def ocr_image(image_bytes: bytes) -> str:
    if not OCR_SPACE_API_KEY:
        return "OCR功能未启用"
    try:
        url = "https://api.ocr.space/parse/image"
        data = {
            "apikey": OCR_SPACE_API_KEY,
            "language": "chs",
            "filetype": "JPG",
            "detectOrientation": True,
            "scale": True
        }
        files = {
            "file": ("image.jpg", image_bytes, "image/jpeg")
        }
        res = requests.post(url, data=data, files=files, timeout=20)
        rj = res.json()

        if rj.get("ParsedResults") and len(rj["ParsedResults"]) > 0:
            txt = rj["ParsedResults"][0]["ParsedText"].strip()
            if txt:
                return txt
        return "未识别到文字"
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return "未识别到文字"

# ---------------------- AI 接口 ----------------------
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
    return "⚠️ 繁忙，请稍后再试"

# ---------------------- 机器人逻辑 ----------------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        mem = context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if mem.status in ["member", "administrator", "creator"]:
            update.message.reply_text("✅ 机器人已启动，支持文字、图片")
        else:
            update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")
    except:
        update.message.reply_text(f"❌ 请先加群\n{GROUP_LINK}")

def reply_message(update: Update, context: CallbackContext):
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

    # 处理图片
    if update.message.photo:
        photo = update.message.photo[-1]
        file = context.bot.get_file(photo.file_id)
        bio = BytesIO()
        file.download(out=bio)
        bio.seek(0)

        img_text = ocr_image(bio.read())
        caption = update.message.caption or "解析这段内容"

        if img_text == "OCR功能未启用":
            update.message.reply_text("🖼️ OCR功能未启用，请检查API Key")
            return
        if img_text == "未识别到文字":
            update.message.reply_text("🖼️ 图片中未识别到可读取的文字")
            return

        full_prompt = f"图片内容：{img_text}\n用户问题：{caption}"
        ai_reply = get_ai_reply(full_prompt)
        update.message.reply_text(f"🖼️ 识别结果：\n{img_text}\n\n🤖 {ai_reply}")
        return

    # 处理文字
    text = update.message.text
    if text:
        update.message.reply_text(get_ai_reply(text))

# ---------------------- 启动 ----------------------
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo | Filters.text & ~Filters.command, reply_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
