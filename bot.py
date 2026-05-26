import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import time
from datetime import datetime, timedelta
import sqlite3
import re

# ============= CONFIGURATION (BAS YAHI CHANGE KARNA HAI) =============
BOT_TOKEN = "8905549650:AAFeUzllz08MA5HKVIKdcY5vfCkEIzRiaSU"

# Owner ka DM Chat ID (owner khud access kar payega)
OWNER_CHAT_ID = 8682114076  # <--- APNI CHAT ID DALO (owner ki)

# Channel join karne ka link (jo owner ne diya)
MAIN_CHANNEL_LINK = "https://t.me/+boavH1Hy_aU5YTFh"

# Owner ka username (jahan users payment ke liye contact karein)
OWNER_USERNAME = "@VIP123CJ"  # <--- APNA USERNAME DALO

# ====================================================================

# Database setup
conn = sqlite3.connect('user_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        joined_main_channel BOOLEAN DEFAULT FALSE,
        access_expiry TIMESTAMP,
        ad_watched_today INTEGER DEFAULT 0,
        last_ad_time TIMESTAMP
    )
''')
conn.commit()

# Channel ke andar ke channels ko check karne ke liye
CHANNELS_TO_JOIN = [
    "https://t.me/+boavH1Hy_aU5YTFh",  # Main channel
    # Yahan aur channels add kar sakte ho agar chaho
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def is_user_in_main_channel(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user has joined main channel"""
    try:
        # Channel username extract karo link se
        match = re.search(r't\.me/([a-zA-Z0-9_]+|\+[a-zA-Z0-9_]+)', MAIN_CHANNEL_LINK)
        if match:
            chat_identifier = match.group(1)
            # Agar private invite link hai (+ se shuru)
            if chat_identifier.startswith('+'):
                return True  # Private link mein check nahi kar sakte, user ko manually join karna hoga
        return True
    except:
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Owner ko special access
    if user_id == OWNER_CHAT_ID:
        await update.message.reply_text(
            "👑 *Owner Access Granted!*\n\n"
            "Aapko unlimited access hai.\n"
            "Bot poora control aapke paas hai.",
            parse_mode="Markdown"
        )
        return
    
    # Check if user already has valid access
    cursor.execute("SELECT access_expiry FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        expiry = datetime.fromisoformat(result[0])
        if expiry > datetime.now():
            remaining = expiry - datetime.now()
            await show_content_access(update, context, remaining)
            return
    
    # Pehle channel join karne ka message
    keyboard = [
        [InlineKeyboardButton("📢 JOIN MAIN CHANNEL", url=MAIN_CHANNEL_LINK)],
        [InlineKeyboardButton("🔄 I HAVE JOINED - REFRESH", callback_data="refresh_channel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ *WELCOME!* ⚠️\n\n"
        "Sabse pehle niche diye gaye channel ko JOIN karo.\n\n"
        f"🔗 Channel Link: {MAIN_CHANNEL_LINK}\n\n"
        "👇 JOIN karne ke baad REFRESH button dabao 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def show_content_access(update: Update, context: ContextTypes.DEFAULT_TYPE, remaining_time=None):
    """Show content after successful access"""
    user_id = update.effective_user.id
    
    if remaining_time is None:
        cursor.execute("SELECT access_expiry FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            expiry = datetime.fromisoformat(result[0])
            if expiry > datetime.now():
                remaining_time = expiry - datetime.now()
            else:
                await start(update, context)
                return
        else:
            await start(update, context)
            return
    
    minutes_left = int(remaining_time.total_seconds() / 60)
    
    keyboard = [
        [InlineKeyboardButton("📂 ACCESS CONTENT NOW 📂", callback_data="view_content")],
        [InlineKeyboardButton("⏰ GET +1 HOUR (Watch 30s Ad)", callback_data="watch_ad")],
        [InlineKeyboardButton("💰 BUY PREMIUM (No Ads)", callback_data="buy_premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ *CHANNEL JOINED SUCCESSFULLY!* ✅\n\n"
        f"🎉 Ab aap content access kar sakte ho!\n"
        f"⏰ Time Left: *{minutes_left} minutes*\n\n"
        f"👇 Neeche diye gaye options mein se koi ek choose karo 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Owner access check
    if user_id == OWNER_CHAT_ID:
        if query.data == "view_content":
            await query.message.reply_text(
                "👑 *Owner Content Panel*\n\n"
                "Yeh raha aapka content...\n\n"
                "• Link 1: [Click Here]\n"
                "• Link 2: [Click Here]\n"
                "• Link 3: [Click Here]",
                parse_mode="Markdown"
            )
        elif query.data == "watch_ad":
            await query.message.reply_text("👑 Owner ko ad nahi dekhna padta!")
        return
    
    if query.data == "refresh_channel":
        # User ne channel join kiya hai maan lo
        cursor.execute("UPDATE users SET joined_main_channel = ? WHERE user_id = ?", (True, user_id))
        conn.commit()
        
        # Ab ad ke liye pucho
        await ask_for_ad(query, context, user_id)
    
    elif query.data == "watch_ad":
        await show_ad_30_seconds(query, context, user_id)
    
    elif query.data == "ad_completed_30s":
        await give_one_hour_access(query, context, user_id)
    
    elif query.data == "buy_premium":
        await show_premium_plans(query, context, user_id)
    
    elif query.data == "view_content":
        await give_content(query, context, user_id)
    
    elif query.data == "contact_owner":
        await contact_owner(query, context, user_id)

async def ask_for_ad(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Ask user to watch ad for 1 hour access"""
    keyboard = [
        [InlineKeyboardButton("🎬 WATCH 30-SECOND AD 🎬", callback_data="watch_ad")],
        [InlineKeyboardButton("💰 BUY PREMIUM (Skip Ads)", callback_data="buy_premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "🎯 *GET 1 HOUR FREE ACCESS!* 🎯\n\n"
        "✅ Aapne channel join kar liya hai!\n"
        "🔐 Ab sirf *30 second ka ad* dekho aur *1 hour* ka access pao.\n\n"
        "👇 Neeche click karo ad dekhne ke liye 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_ad_30_seconds(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show 30 second ad simulation"""
    ad_link = "https://example.com/ad/30-second-ad"
    
    message = (
        "📺 *30 SECOND AD* 📺\n\n"
        "👇 *Is link par click karo aur ad dekho:*\n"
        f"[🎬 CLICK HERE TO WATCH 30s AD]({ad_link})\n\n"
        "⚠️ *Ad complete hone ke baad neeche COMPLETE button dabao!*\n"
        "⏱️ Ad exactly 30 seconds ka hai."
    )
    
    keyboard = [[InlineKeyboardButton("✅ AD COMPLETE - GIVE 1 HOUR ✅", callback_data="ad_completed_30s")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.user_data['ad_start_time'] = time.time()
    
    await query.message.edit_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def give_one_hour_access(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Give 1 hour access after ad completion"""
    # Optional: Check if 30 seconds passed
    if 'ad_start_time' in context.user_data:
        elapsed = time.time() - context.user_data['ad_start_time']
        if elapsed < 25:
            remaining = int(30 - elapsed)
            await query.message.reply_text(f"⏳ Please wait {remaining} more seconds to complete the ad!")
            return
    
    expiry = datetime.now() + timedelta(hours=1)
    
    cursor.execute("""
        INSERT INTO users (user_id, joined_main_channel, access_expiry, ad_watched_today) 
        VALUES (?, ?, ?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET 
        access_expiry = excluded.access_expiry
    """, (user_id, True, expiry.isoformat(), 1))
    conn.commit()
    
    keyboard = [
        [InlineKeyboardButton("📂 VIEW CONTENT NOW 📂", callback_data="view_content")],
        [InlineKeyboardButton("🎬 GET ANOTHER +1 HOUR", callback_data="watch_ad")],
        [InlineKeyboardButton("💰 BUY PREMIUM (No Ads Forever)", callback_data="buy_premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"✅ *ACCESS GRANTED!* ✅\n\n"
        f"🎉 Aapko *1 hour* ka access mil gaya!\n"
        f"⏰ Expires at: {(datetime.now() + timedelta(hours=1)).strftime('%I:%M %p')}\n\n"
        f"👇 Ab content dekhne ke liye neeche click karo 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_premium_plans(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show premium purchase plans"""
    plans = (
        "💰 *PREMIUM PLANS - NO ADS* 💰\n\n"
        "✨ *7 Days* – ₹49 (168 hours)\n"
        "✨ *1 Month* – ₹189 (720 hours)\n"
        "✨ *3 Months* – ₹389 (2160 hours)\n"
        "✨ *6 Months* – ₹689 (4320 hours)\n"
        "✨ *9 Months* – ₹800 (6480 hours)\n"
        "✨ *12 Months* – ₹999 (8640 hours)\n\n"
        "📞 *Premium lene ke liye owner se contact karo:*\n"
        f"{OWNER_USERNAME}\n\n"
        "👇 Neeche click karo owner se baat karne ke liye 👇"
    )
    
    keyboard = [[InlineKeyboardButton("📩 CONTACT OWNER FOR PREMIUM 📩", callback_data="contact_owner")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(plans, reply_markup=reply_markup, parse_mode="Markdown")

async def contact_owner(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Forward user to owner DM"""
    message = (
        f"👤 New User wants Premium!\n"
        f"User ID: `{user_id}`\n"
        f"Username: @{query.from_user.username if query.from_user.username else 'No username'}\n\n"
        f"Reply to this user to process payment."
    )
    
    try:
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=message, parse_mode="Markdown")
        await query.message.reply_text(
            f"✅ *Owner ko notification bhej di gayi!*\n\n"
            f"Owner jald hi aapse contact karega.\n"
            f"Aap directly bhi contact kar sakte ho: {OWNER_USERNAME}",
            parse_mode="Markdown"
        )
    except:
        await query.message.reply_text(
            f"📞 *Contact Owner Directly:*\n{OWNER_USERNAME}\n\n"
            f"Owner ko DM karo premium lene ke liye.",
            parse_mode="Markdown"
        )

async def give_content(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Give actual content access"""
    # Check if user has valid access
    cursor.execute("SELECT access_expiry FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        expiry = datetime.fromisoformat(result[0])
        if expiry > datetime.now():
            remaining = expiry - datetime.now()
            minutes_left = int(remaining.total_seconds() / 60)
            
            content = (
                f"🔓 *CONTENT ACCESS* 🔓\n\n"
                f"✅ Aapke paas {minutes_left} minutes ka access hai!\n\n"
                f"📁 *Available Content:*\n"
                f"• [Link 1 - Join Channel](https://t.me/+boavH1Hy_aU5YTFh)\n"
                f"• [Link 2 - WhatsApp Group](https://whatsapp.com/channel/...)\n"
                f"• [Link 3 - Telegram Channel](https://t.me/...)\n\n"
                f"⏰ Time left: {minutes_left} minutes\n\n"
                f"💡 /ad - Watch ad for +1 hour\n"
                f"💰 /premium - Buy premium (no ads)"
            )
            
            await query.message.reply_text(content, parse_mode="Markdown", disable_web_page_preview=True)
            return
    
    # No access
    await start(update, ContextTypes.DEFAULT_TYPE())
    # We need to handle this properly
    await query.message.reply_text("❌ Aapka access expired ho gaya hai! /start karo naye access ke liye.")

async def ad_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual /ad command"""
    user_id = update.effective_user.id
    
    if user_id == OWNER_CHAT_ID:
        await update.message.reply_text("👑 Owner - Aapko ad ki zaroorat nahi!")
        return
    
    # Check if user has joined channel
    cursor.execute("SELECT joined_main_channel FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        # Create a callback query-like message
        class MockQuery:
            def __init__(self, message):
                self.message = message
            async def answer(self):
                pass
            async def edit_text(self, text, reply_markup=None, parse_mode=None):
                await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        
        mock_query = MockQuery(update.message)
        await show_ad_30_seconds(mock_query, context, user_id)
    else:
        await start(update, context)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual /premium command"""
    user_id = update.effective_user.id
    
    plans = (
        "💰 *PREMIUM PLANS - NO ADS* 💰\n\n"
        "✨ 7 Days – ₹49\n"
        "✨ 1 Month – ₹189\n"
        "✨ 3 Months – ₹389\n"
        "✨ 6 Months – ₹689\n"
        "✨ 9 Months – ₹800\n"
        "✨ 12 Months – ₹999\n\n"
        f"📞 Contact: {OWNER_USERNAME}"
    )
    
    await update.message.reply_text(plans, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ad", ad_command))
    app.add_handler(CommandHandler("premium", premium_command))
    
    # Button handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 BOT IS RUNNING...")
    print(f"📢 Main Channel: {MAIN_CHANNEL_LINK}")
    print(f"👑 Owner Chat ID: {OWNER_CHAT_ID}")
    
    app.run_polling()

if __name__ == "__main__":
    main()