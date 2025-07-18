import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from datetime import datetime

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('afk_users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS afk_users
                 (username TEXT PRIMARY KEY, reason TEXT, time TEXT)''')
    conn.commit()
    conn.close()

# Store AFK user
def set_afk(username, reason, time):
    conn = sqlite3.connect('afk_users.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO afk_users (username, reason, time) VALUES (?, ?, ?)",
              (username, reason, time))
    conn.commit()
    conn.close()

# Remove AFK user
def remove_afk(username):
    conn = sqlite3.connect('afk_users.db')
    c = conn.cursor()
    c.execute("DELETE FROM afk_users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

# Check if user is AFK
def get_afk(username):
    conn = sqlite3.connect('afk_users.db')
    c = conn.cursor()
    c.execute("SELECT reason, time FROM afk_users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your Tag & AFK bot. Use /tag [message], /afk [reason], or /back.")

async def tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.message.chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command works in groups only! 😕")
        return

    args = context.args
    message = " ".join(args) if args else "Hey! 😎"  # Default message with emoji
    # Get group admins
    admins = await chat.get_administrators()
    tags = " ".join([f"@{admin.user.username}" for admin in admins if admin.user.username])
    await update.message.reply_text(f"{message}\nTagged: {tags}")

async def afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = user.username
    if not username:
        await update.message.reply_text("You need a Telegram username to use AFK! 😕")
        return

    reason = " ".join(context.args) if context.args else "No reason provided"
    time = datetime.now().isoformat()
    set_afk(username, reason, time)
    await update.message.reply_text(f"@{username} is now AFK: {reason} 😴")

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = user.username
    if not username:
        await update.message.reply_text("You need a Telegram username to use this! 😕")
        return

    if get_afk(username):
        remove_afk(username)
        await update.message.reply_text(f"Welcome back, @{username}! 🎉")
    else:
        await update.message.reply_text(f"@{username}, you weren't AFK! 😕")

async def check_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.entities:
        return

    for entity in message.entities:
        if entity.type == "mention":
            username = message.text[entity.offset + 1:entity.offset + entity.length].replace("@", "")
            afk_data = get_afk(username)
            if afk_data:
                reason, time = afk_data
                await message.reply_text(f"@{username} is AFK: {reason} (since {time}) 😴")

def main():
    # Initialize database
    init_db()
    # Your bot token
    token = os.getenv("BOT_TOKEN", "8115638159:AAEvHb0ePXLgTczR32JPPVgz45LM8sG3zRk")
    app = Application.builder().token(token).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tag", tag))
    app.add_handler(CommandHandler("afk", afk))
    app.add_handler(CommandHandler("back", back))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_afk))

    # Start the bot
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()