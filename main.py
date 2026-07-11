import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Define Conversation States
SELECT_QUANTITY, SELECT_COIN, CONFIRM_PAYMENT = range(3)

# Base price per plan unit in USD
UNIT_PRICE = 18  

# --- WALLET CONFIGURATION ---
# (You can also set these inside Railway Environment Variables)
USDT_TRC20 = os.getenv("USDT_TRC20", "Your_USDT_TRC20_Wallet_Address_Here")
BTC_WALLET = os.getenv("BTC_WALLET", "Your_Bitcoin_Wallet_Address_Here")
LTC_WALLET = os.getenv("LTC_WALLET", "Your_Litecoin_Wallet_Address_Here")

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main landing menu with quick commands."""
    welcome_text = (
        "🚀 *Welcome to the FXReplay Pro Sales Bot!*\n\n"
        "Get instant access to FXReplay Pro accounts at discounted rates.\n"
        "Select an option below to get started or buy directly:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📊 Plan Details", callback_data="cmd_plan"), InlineKeyboardButton("💵 Pricing", callback_data="cmd_price")],
        [InlineKeyboardButton("🚚 Delivery Mode", callback_data="cmd_delivery"), InlineKeyboardButton("💳 Buy Now (Checkout)", callback_data="cmd_buy")],
        [InlineKeyboardButton("💬 Support Agent", url="https://t.me/your_telegram_username")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def plan_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *FXReplay Pro Plan Features*\n\n"
        "• Unlimited Backtesting Sessions & Trades\n"
        "• Access to Seconds Timeframes (1s, 5s, etc.)\n"
        "• Unlimited Multi-chart Layouts & Indicators\n"
        "• Futures, Stocks, Forex & Crypto Data\n"
        "• Built-in Prop Firm Challenge Simulator\n"
        "• Mentor AI & Advanced Analytics\n"
    )
    await send_or_edit(update, text)

async def price_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💵 *Discounted Pricing*\n\n"
        f"• *Official FXReplay Pro:* $35/month\n"
        f"• *Our Offer:* **${UNIT_PRICE}/month** (Save 50%!)\n\n"
        "Need multiple accounts? Click **Buy Now** to select quantity."
    )
    await send_or_edit(update, text)

async def delivery_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚚 *Delivery Mode & Warranty*\n\n"
        "• *Speed:* Credentials delivered within 5–15 mins after admin payment verification.\n"
        "• *Format:* Private Email + Password details sent directly to your Telegram chat.\n"
        "• *Warranty:* Full replacement guarantee for the length of your subscription."
    )
    await send_or_edit(update, text)

# --- CHECKOUT CONVERSATION FLOW ---

async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Select Quantity."""
    text = "🛒 *Checkout - Step 1/3*\n\nHow many FXReplay Pro monthly accounts would you like to purchase?"
    
    keyboard = [
        [InlineKeyboardButton("1 Account ($18)", callback_data="qty_1"), InlineKeyboardButton("2 Accounts ($36)", callback_data="qty_2")],
        [InlineKeyboardButton("3 Accounts ($54)", callback_data="qty_3"), InlineKeyboardButton("5 Accounts ($90)", callback_data="qty_5")],
        [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        
    return SELECT_QUANTITY

async def quantity_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save quantity and choose Crypto Wallet."""
    query = update.callback_query
    await query.answer()
    
    qty = int(query.data.split("_")[1])
    total_usd = qty * UNIT_PRICE
    
    # Store order info in context memory
    context.user_data["quantity"] = qty
    context.user_data["total_usd"] = total_usd
    
    text = (
        f"💳 *Checkout - Step 2/3*\n\n"
        f"• *Quantity:* {qty} Account(s)\n"
        f"• *Total Due:* **${total_usd} USD**\n\n"
        f"Select your preferred cryptocurrency to pay:"
    )
    
    keyboard = [
        [InlineKeyboardButton("USDT (TRC20)", callback_data="coin_USDT")],
        [InlineKeyboardButton("Bitcoin (BTC)", callback_data="coin_BTC"), InlineKeyboardButton("Litecoin (LTC)", callback_data="coin_LTC")],
        [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    return SELECT_COIN

async def coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Show wallet address and present payment confirmation button."""
    query = update.callback_query
    await query.answer()
    
    coin = query.data.split("_")[1]
    context.user_data["coin"] = coin
    
    qty = context.user_data["quantity"]
    total_usd = context.user_data["total_usd"]
    
    wallet_address = USDT_TRC20 if coin == "USDT" else (BTC_WALLET if coin == "BTC" else LTC_WALLET)
    
    text = (
        f"⚡ *Payment Instructions - Step 3/3*\n\n"
        f"Please send **${total_usd} USD** equivalent of **{coin}** to the address below:\n\n"
        f"📌 *{coin} Wallet Address:*\n`{wallet_address}`\n\n"
        f"⚠️ *Important:* After sending payment, tap the **I Have Paid** button below to notify our admin team immediately."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ I Have Paid", callback_data="confirm_paid")],
        [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    return CONFIRM_PAYMENT

async def payment_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final Step: Notify User and Alert Admin instantly."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    username = f"@{user.username}" if user.username else "No Username"
    user_id = user.id
    
    qty = context.user_data.get("quantity", 1)
    total_usd = context.user_data.get("total_usd", 18)
    coin = context.user_data.get("coin", "USDT")
    
    # 1. Message sent to Customer
    await query.message.reply_text(
        "🎉 *Payment Notification Submitted!*\n\n"
        "Our admin team has been notified. Once confirmed on the blockchain, your account credentials "
        "will be delivered right here in this chat.\n\n"
        "If you have transaction screenshots, you can also send them directly to our support agent.",
        parse_mode="Markdown"
    )
    
    # 2. Alert sent to ADMIN via Telegram
    ADMIN_ID = os.getenv("ADMIN_ID")
    if ADMIN_ID:
        admin_alert_text = (
            "🚨 *NEW ORDER PAYMENT ALERT!* 🚨\n\n"
            f"👤 *Customer:* {username} (ID: `{user_id}`)\n"
            f"📦 *Quantity:* {qty} FXReplay Account(s)\n"
            f"💰 *Amount Due:* ${total_usd} USD\n"
            f"🪙 *Coin Chosen:* {coin}\n\n"
            f"👉 *Action Required:* Check blockchain, then DM user: [{user.first_name}](tg://user?id={user_id})"
        )
        try:
            await context.bot.send_message(chat_id=int(ADMIN_ID), text=admin_alert_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Failed to alert admin: {e}")
            
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels checkout flow."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ Order cancelled. Type /start anytime to return to the main menu.")
    return ConversationHandler.END

# --- UTILITIES ---

async def send_or_edit(update: Update, text: str):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

# --- MAIN ENGINE ---

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN variable is missing!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation Handler for Interactive Checkout
    buy_conv = ConversationHandler(
        entry_points=[
            CommandHandler("buy", start_buy),
            CallbackQueryHandler(start_buy, pattern="^cmd_buy$")
        ],
        states={
            SELECT_QUANTITY: [CallbackQueryHandler(quantity_selected, pattern="^qty_")],
            SELECT_COIN: [CallbackQueryHandler(coin_selected, pattern="^coin_")],
            CONFIRM_PAYMENT: [CallbackQueryHandler(payment_confirmed, pattern="^confirm_paid$")]
        },
        fallbacks=[CallbackQueryHandler(cancel_order, pattern="^cancel_order$")]
    )

    # General Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan_details))
    app.add_handler(CommandHandler("price", price_details))
    app.add_handler(CommandHandler("delivery", delivery_mode))
    
    app.add_handler(CallbackQueryHandler(plan_details, pattern="^cmd_plan$"))
    app.add_handler(CallbackQueryHandler(price_details, pattern="^cmd_price$"))
    app.add_handler(CallbackQueryHandler(delivery_mode, pattern="^cmd_delivery$"))
    
    # Add Checkout Handler
    app.add_handler(buy_conv)

    print("🤖 FXReplay Checkout Bot with Admin Alerts is Online...")
    app.run_polling()

if __name__ == "__main__":
    main()
