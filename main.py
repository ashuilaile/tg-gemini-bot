import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ===================== 环境变量 =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
# =====================================================

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
    """轮询多个AI接口，确保成功"""
    ais = [ask_gemini, ask_deepseek, ask_siliconflow]
    random.shuffle(ais)
    for func in ais:
        res = func(prompt)
        if res:
            return res
    return "⚠️ 所有AI接口暂时繁忙，请稍后再试~"

# ---------------------- 命令处理 ----------------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("✅ 机器人已启动！现在可以直接发送文字提问~")

def handle_text(update: Update, context: CallbackContext):
    """只处理文字消息，完全不处理图片/文件"""
    user_text = update.message.text
    ai_reply = get_ai_reply(user_text)
    update.message.reply_text(ai_reply)

# ---------------------- 主函数 ----------------------
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    # 只监听文字消息，完全不监听图片/文件
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
