import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with interactive command buttons."""
    welcome_text = (
        "🚀 *Welcome to the FXReplay Pro Sales Bot!*\n\n"
        "Get instant access to FXReplay Pro at discounted rates.\n"
        "Use the menu below or type commands to navigate:"
    )
    
    # Inline buttons for quick tapping
    keyboard = [
        [InlineKeyboardButton("📊 Plan Details", callback_data="plan_details"), InlineKeyboardButton("💵 Pricing", callback_data="pricing")],
        [InlineKeyboardButton("🚚 Delivery Mode", callback_data="delivery"), InlineKeyboardButton("💳 Payment Methods", callback_data="payment")],
        [InlineKeyboardButton("💬 Buy Now / Contact Support", url="https://t.me/your_telegram_username")] # Replace with your username
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def plan_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *FXReplay Pro Plan Details*\n\n"
        "FXReplay is the premier TradingView-powered backtesting & market replay platform.\n\n"
        "⚡ *Pro Features Included:*\n"
        "• Unlimited Backtesting Sessions & Trades\n"
        "• Access to Seconds Timeframe (1s, 5s, etc.)\n"
        "• Unlimited Multi-chart Layouts & Indicators\n"
        "• Full Futures, Forex, Crypto & Stocks Data\n"
        "• Built-in Prop Firm Challenge Simulator\n"
        "• Mentor AI & Advanced Analytics\n"
        "• Spreads & Commission Simulation\n"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def price_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💵 *FXReplay Pro Pricing*\n\n"
        "• *Official FXReplay Price:* $35 / month\n"
        "• *Our Discounted Price:* **$18 / month** (Save ~50%!)\n"
        "• *3-Month Plan:* **$45**\n"
        "• *1-Year Plan:* **$140**\n\n"
        "✅ 100% Genuine Private Account / Shared Option available."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def delivery_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚚 *Delivery Mode & Speed*\n\n"
        "• *Delivery Time:* Instantly within 5–15 minutes after payment verification.\n"
        "• *Format:* You will receive login credentials (Email + Password) directly in private chat.\n"
        "• *Warranty:* Full replacement warranty for the duration of your active subscription plan."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def payment_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💳 *Supported Payment Methods*\n\n"
        "We accept multiple secure payment modes:\n"
        "1. **Crypto:** USDT (TRC20 / BEP20), BTC, LTC\n"
        "2. **UPI / GPay / PhonePe:** (For Indian Users)\n"
        "3. **Binance Pay:** (Zero fees)\n"
        "4. **PayPal:** (Friends & Family)\n\n"
        "📩 Ready to purchase? Click below to send a message to our agent."
    )
    keyboard = [[InlineKeyboardButton("📩 Contact Seller to Pay", url="https://t.me/your_telegram_username")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# --- BUTTON CALLBACK HANDLER ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "plan_details":
        await plan_details(update, context)
    elif query.data == "pricing":
        await price_details(update, context)
    elif query.data == "delivery":
        await delivery_mode(update, context)
    elif query.data == "payment":
        await payment_methods(update, context)

# --- MAIN ENGINE ---

def main():
    # Reads token safely from environment variables
    BOT_TOKEN = os.getenv("8612352765:AAFeD_hRqZyMuUHRyiTVn4sJYZIIhCZkh4M")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan_details))
    app.add_handler(CommandHandler("price", price_details))
    app.add_handler(CommandHandler("delivery", delivery_mode))
    app.add_handler(CommandHandler("payment", payment_methods))

    # Register Button Callback Handler
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 FXReplay Sales Bot is online and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
