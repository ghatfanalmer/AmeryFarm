import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8849303777:AAF5inJxsdtE6DrTB4BPpQ2Uy986brh89Mo"

# Server Flask kecil untuk menjaga bot tetap aktif di Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Telegram @AmeryFarm_Bot Aktif!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Bot sudah aktif.")

if __name__ == '__main__':
    # Jalankan server web di background
    Thread(target=run_web).start()

    # Jalankan bot Telegram
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.run_polling()
