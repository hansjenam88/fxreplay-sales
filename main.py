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
SELECT_QUANTITY, MANUAL_FLOW = range(2)

# --- ENVIRONMENT VARIABLES & CONFIGURATION ---
UNIT_PRICE = float(os.getenv("UNIT_PRICE", "1.5"))  

LTC_WALLET = os.getenv("LTC_WALLET", "Your_Litecoin_Wallet_Address_Here")
SOL_WALLET = os.getenv("SOL_WALLET", "Your_Solana_Wallet_Address_Here")

# --- HELPER UTILITY FOR MAIN MENU NAVIGATION ---

async def edit_or_reply(update: Update, text: str, reply_markup: InlineKeyboardMarkup = None):
    """Edits main menu messages in-place to keep navigation clean."""
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception:
            pass
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# --- MAIN NAVIGATION COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🚀 *Welcome to the FXReplay Pro Sales Bot!*\n\n"
        "Get instant access to FXReplay Pro accounts at discounted rates.\n"
        "Select an option below to navigate or tap **Buy Now** to place an order:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📊 Plan Details", callback_data="cmd_plan"), InlineKeyboardButton("💵 Pricing", callback_data="cmd_price")],
        [InlineKeyboardButton("🚚 Delivery Mode", callback_data="cmd_delivery"), InlineKeyboardButton("💳 Buy Now (Checkout)", callback_data="cmd_buy")],
        [InlineKeyboardButton("💬 Support Agent", url="https://t.me/your_telegram_username")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await edit_or_reply(update, welcome_text, reply_markup)

async def plan_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *FXReplay Pro Plan Features*\n\n"
        "• Unlimited Backtesting Sessions & Trades\n"
        "• Access to Seconds Timeframes (1s, 5s, etc.)\n"
        "• Unlimited Multi-chart Layouts & Indicators\n"
        "• Futures, Stocks, Forex & Crypto Data\n"
        "• Built-in Prop Firm Challenge Simulator\n"
        "• Mentor AI & Advanced Analytics"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="cmd_start")]]
    await edit_or_reply(update, text, InlineKeyboardMarkup(keyboard))

async def price_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💵 *Discounted Pricing*\n\n"
        "• *Official FXReplay Pro:* $30 / month\n"
        "                                            $5 / 5 days\n\n"
        f"• *Our Price:* **${UNIT_PRICE:.1f} / 5 days**\n\n"
        "Need multiple accounts? Tap **Buy Now** to start checkout."
    )
    keyboard = [
        [InlineKeyboardButton("💳 Buy Now", callback_data="cmd_buy")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="cmd_start")]
    ]
    await edit_or_reply(update, text, InlineKeyboardMarkup(keyboard))

async def delivery_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚚 *Delivery Mode & Warranty*\n\n"
        "• *Speed:* Credentials delivered within 5–15 mins after payment verification.\n"
        "• *Format:* Private Email + Password details sent directly to your Telegram chat.\n"
        "• *Warranty:* Full replacement guarantee for the duration of your active plan."
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="cmd_start")]]
    await edit_or_reply(update, text, InlineKeyboardMarkup(keyboard))

# --- CHECKOUT FLOW (SPAWNS NEW MESSAGE) ---

async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Spawns a NEW stacked message block specifically for Checkout."""
    p = UNIT_PRICE
    text = "🛒 *Checkout - Step 1/2*\n\nHow many FXReplay Pro accounts would you like to purchase?"
    
    keyboard = [
        [InlineKeyboardButton(f"1 Account (${p*1:.2f})", callback_data="qty_1"), InlineKeyboardButton(f"2 Accounts (${p*2:.2f})", callback_data="qty_2")],
        [InlineKeyboardButton(f"3 Accounts (${p*3:.2f})", callback_data="qty_3"), InlineKeyboardButton(f"5 Accounts (${p*5:.2f})", callback_data="qty_5")],
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
    """Step 2: Saves quantity and displays payment wallet details directly."""
    query = update.callback_query
    await query.answer()
    
    qty = int(query.data.split("_")[1])
    total_usd = qty * UNIT_PRICE
    
    context.user_data["quantity"] = qty
    context.user_data["total_usd"] = total_usd
    
    text = (
        f"⚡ *Checkout - Step 2/2 (Payment)*\n\n"
        f"• *Quantity:* {qty} Account(s)\n"
        f"• *Total Due:* **${total_usd:.2f} USD**\n\n"
        f"Please send **${total_usd:.2f} USD** to one of our official wallet addresses below:\n\n"
        f"🪙 *Litecoin (LTC):*\n`{LTC_WALLET}`\n\n"
        f"🪙 *Solana (SOL):*\n`{SOL_WALLET}`\n\n"
        f"⚠️ *Note:* Tap any address above to copy it instantly. After making the deposit, tap **I Have Paid** below."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ I Have Paid", callback_data="confirm_manual_paid")],
        [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    return MANUAL_FLOW

async def manual_payment_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final Step: Alerts user and sends notification to Admin."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    username = f"@{user.username}" if user.username else "No Username"
    qty = context.user_data.get("quantity", 1)
    total_usd = context.user_data.get("total_usd", UNIT_PRICE)
    
    await query.edit_message_text(
        "🎉 *Payment Notification Submitted!*\n\n"
        "Our admin team has been notified. Once confirmed on the blockchain, your account credentials "
        "will be delivered right here in this chat.",
        parse_mode="Markdown"
    )
    
    ADMIN_ID = os.getenv("ADMIN_ID")
    if ADMIN_ID:
        admin_alert_text = (
            "🚨 *NEW PAYMENT ALERT!* 🚨\n\n"
            f"👤 *Customer:* {username} (ID: `{user.id}`)\n"
            f"📦 *Quantity:* {qty} FXReplay Account(s)\n"
            f"💰 *Amount Due:* ${total_usd:.2f} USD\n"
            f"💳 *Method:* Manual Wallet Transfer (LTC / SOL)\n\n"
            f"👉 *Action Required:* Verify on blockchain and DM user: [{user.first_name}](tg://user?id={user.id})"
        )
        try:
            await context.bot.send_message(chat_id=int(ADMIN_ID), text=admin_alert_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Failed to alert admin: {e}")
            
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Order cancelled. Type /start anytime to return to the main menu.")
    return ConversationHandler.END

# --- MAIN ENGINE ---

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN variable is missing!")

    app = Application.builder().token(BOT_TOKEN).build()

    buy_conv = ConversationHandler(
        entry_points=[
            CommandHandler("buy", start_buy),
            CallbackQueryHandler(start_buy, pattern="^cmd_buy$")
        ],
        states={
            SELECT_QUANTITY: [CallbackQueryHandler(quantity_selected, pattern="^qty_")],
            MANUAL_FLOW: [CallbackQueryHandler(manual_payment_confirmed, pattern="^confirm_manual_paid$")]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_order, pattern="^cancel_order$"),
            CallbackQueryHandler(start, pattern="^cmd_start$")
        ]
    )

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan_details))
    app.add_handler(CommandHandler("price", price_details))
    app.add_handler(CommandHandler("delivery", delivery_mode))
    
    app.add_handler(CallbackQueryHandler(start, pattern="^cmd_start$"))
    app.add_handler(CallbackQueryHandler(plan_details, pattern="^cmd_plan$"))
    app.add_handler(CallbackQueryHandler(price_details, pattern="^cmd_price$"))
    app.add_handler(CallbackQueryHandler(delivery_mode, pattern="^cmd_delivery$"))
    
    app.add_handler(buy_conv)

    print("🤖 Streamlined FXReplay Sales Bot Online...")
    app.run_polling()

if __name__ == "__main__":
    main()
