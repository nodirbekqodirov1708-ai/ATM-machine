import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8773377723:AAEPmTf-brGR0V-_RnDqIGYI8xaG_vUi_Eo"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to DoubleDripStore! 👟👕")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("What are you looking for?\n\n👟 /shoes\n👕 /clothes")

async def shoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("No available shoes yet")

async def clothes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("No available clothes yet")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here's the contact")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("shoes", shoes))
    app.add_handler(CommandHandler("clothes", clothes))
    app.add_handler(CommandHandler("contact", contact))
    print("DoubleDripStore bot is running...")
    app.run_polling()








