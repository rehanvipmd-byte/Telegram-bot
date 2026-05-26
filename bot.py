import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import time
from datetime import datetime, timedelta
import sqlite3
import os

BOT_TOKEN = "8905549650:AAFeUzllz08MA5HKVIKdcY5vfCkEIzRiaSU"
OWNER_CHAT_ID = 8682114076
MAIN_CHANNEL_LINK = "https://t.me/+boavH1Hy_aU5YTFh"
OWNER_USERNAME = "@VIP123CJ"

conn = sqlite3.connect('user_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        joined_main_channel BOOLEAN DEFAULT FALSE,
        access_expiry TIMESTAMP
    )
''')
conn.commit()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update, context):
    user_id = update.effective_user.id
    if user_id == OWNER_CHAT_ID:
        await update.message.reply_text("👑 Owner Access Granted!")
        return
    
    keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url=MAIN_CHANNEL_LINK)],
                [InlineKeyboardButton("🔄 I HAVE JOINED", callback_data="joined")]]
    await update.message.reply_text("⚠️ Please join the channel first:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "joined":
        await query.message.reply_text("✅ Channel joined! Now /watchad for 1 hour access.")

async def watch_ad(update, context):
    user_id = update.effective_user.id
    if user_id == OWNER_CHAT_ID:
        await update.message.reply_text("👑 No ads for owner!")
        return
    
    expiry = datetime.now() + timedelta(hours=1)
    cursor.execute("INSERT OR REPLACE INTO users (user_id, joined_main_channel, access_expiry) VALUES (?, ?, ?)",
                   (user_id, True, expiry.isoformat()))
    conn.commit()
    await update.message.reply_text(f"✅ 1 hour access granted! Expires at {expiry.strftime('%H:%M:%S')}\nUse /start again after expiry.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("watchad", watch_ad))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
