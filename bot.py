import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from pymongo import MongoClient
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Database setup
client = MongoClient(os.getenv('MONGODB_URL'))
db = client['telegram_membership']
users_collection = db['users']
channels_collection = db['channels']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Telegram Membership Bot!")

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and len(context.args) == 2:
        name, url = context.args
        channels_collection.insert_one({'name': name, 'url': url})
        await update.message.reply_text(f"Channel '{name}' added successfully.")
    else:
        await update.message.reply_text("Usage: /addchannel name:url")

async def show_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = channels_collection.find()
    keyboard = [[InlineKeyboardButton(channel['name'], url=channel['url'])] for channel in channels]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Available Channels:", reply_markup=reply_markup)

async def approveme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Implement logic to accept all join requests
    await update.message.reply_text("All join requests have been accepted.")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and len(context.args) == 2:
        user_id, expiry_date = context.args
        expiry_date = datetime.strptime(expiry_date, '%d/%m/%Y')
        users_collection.insert_one({'user_id': user_id, 'expiry_date': expiry_date})
        await update.message.reply_text(f"User {user_id} added as premium until {expiry_date}.")
    else:
        await update.message.reply_text("Usage: /adduser userid expiry_date")

async def days_remaining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].isdigit():
        user_id = context.args[0]
        user = users_collection.find_one({'user_id': user_id})
        if user:
            remaining_days = (user['expiry_date'] - datetime.now()).days
            await update.message.reply_text(f"{remaining_days} days remaining for user {user_id}.")
        else:
            await update.message.reply_text("User not found.")
    else:
        await update.message.reply_text("Usage: /daysremaining userid")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == int(os.getenv('OWNER_ID')):  # Ensure OWNER_ID is an integer
        users = users_collection.find()
        for user in users:
            remaining_days = (user['expiry_date'] - datetime.now()).days
            await context.bot.send_message(user['user_id'], f"You have {remaining_days} days remaining.")
        await update.message.reply_text("Reminders sent to all premium users.")
    else:
        await update.message.reply_text("You are not authorized to use this command.")

def main():
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addchannel", add_channel))
    application.add_handler(CommandHandler("channels", show_channels))
    application.add_handler(CommandHandler("approveme", approveme))
    application.add_handler(CommandHandler("adduser", add_user))
    application.add_handler(CommandHandler("daysremaining", days_remaining))
    application.add_handler(CommandHandler("remind", remind))

    application.run_polling()

if __name__ == '__main__':
    main()
