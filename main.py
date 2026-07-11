import os
import logging
from aiocryptopay import AioCryptoPay, Networks
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
SELECT_QUANTITY, SELECT_METHOD, CRYPTOBOT_FLOW, MANUAL_FLOW = range(4)

# --- ENVIRONMENT VARIABLES & CONFIGURATION ---
UNIT_PRICE = float(os.getenv("UNIT_PRICE", "18"))  

CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET) if CRYPTO_TOKEN else None

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
        "• *Official FXReplay Pro:* $35/month\n"
        f"• *Our Offer:* **${UNIT_PRICE:.2f}/month** (Save 50%!)\n\n"
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
    text = "🛒 *Checkout - Step 1/3*\n\nHow many FXReplay Pro monthly accounts would you like to purchase?"
    
    keyboard = [
        [InlineKeyboardButton(f"1 Account (${p*1:.0f})", callback_data="qty_1"), InlineKeyboardButton(f"2 Accounts (${p*2:.0f})", callback_data="qty_2")],
        [InlineKeyboardButton(f"3 Accounts (${p*3:.0f})", callback_data="qty_3"), InlineKeyboardButton(f"5 Accounts (${p*5:.0f})", callback_data="qty_5")],
        [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send as a brand NEW message instead of editing the menu
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        
    return SELECT_QUANTITY

async def quantity_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Updates the Checkout card in-place for steps 2 & 3."""
    query = update.callback_query
    await query.answer()
    
    qty = int(query.data.split("_")[1])
    total_usd = qty * UNIT_PRICE
    
    context.user_data["quantity"] = qty
    context.user_data["total_usd"] = total_usd
    
    text = (
        f"💳 *Checkout - Step 2/3*\n\n"
        f"• *Quantity:* {qty} Account(s)\n"
        f"• *Total Due:* **${total_usd:.2f} USD**\n\n"
        f"Select your preferred payment gateway:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🤖 Pay via Crypto Bot (@CryptoBot)", callback_data="method_cryptobot")],
        [InlineKeyboardButton("✋ Pay Manually to Wallet (LTC / SOL)", callback_data="method_manual")],
        [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    return SELECT_METHOD

# --- OPTION A: CRYPTO BOT API FLOW ---

async def cryptobot_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not crypto:
        await query.edit_message_text("⚠️ Crypto Bot API Token is missing in Railway variables! Please select manual payment.")
        return SELECT_METHOD

    total_usd = context.user_data.get("total_usd", UNIT_PRICE)
    qty = context.user_data.get("quantity", 1)
    
    try:
        invoice = await crypto.create_invoice(
            asset="USDT",
            amount=total_usd,
            description=f"Purchase of {qty} FXReplay Pro Account(s)",
            payload=f"user_{query.from_user.id}"
        )
        context.user_data["invoice_id"] = invoice.invoice_id
        
        text = (
            f"⚡ *Crypto Bot Payment Invoice Created!*\n\n"
            f"• *Amount Due:* **${total_usd:.2f} USD**\n"
            f"• *Invoice ID:* `{invoice.invoice_id}`\n\n"
            f"Tap the button below to complete payment inside Telegram using `@CryptoBot`.\n"
            f"Once complete, tap **Check Payment Status** below."
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Pay via @CryptoBot", url=invoice.bot_invoice_url)],
            [InlineKeyboardButton("🔍 Check Payment Status", callback_data="check_crypto_status")],
            [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        return CRYPTOBOT_FLOW
    except Exception as e:
        logging.error(f"Crypto Bot Invoice Error: {e}")
        await query.edit_message_text("❌ Failed to generate Crypto Bot invoice. Please try Manual Wallet Payment.")
        return SELECT_METHOD

async def check_crypto_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    invoice_id = context.user_data.get("invoice_id")
    if not invoice_id or not crypto:
        await query.answer("❌ Active invoice not found.", show_alert=True)
        return CRYPTOBOT_FLOW

    invoices = await crypto.get_invoices(invoice_ids=invoice_id)
    if invoices and invoices[0].status == "paid":
        await query.answer()
        user = query.from_user
        username = f"@{user.username}" if user.username else "No Username"
        qty = context.user_data.get("quantity", 1)
        total_usd = context.user_data.get("total_usd", UNIT_PRICE)
        
        await query.edit_message_text(
            "🎉 *Payment Verified Successfully!*\n\n"
            "Your order has been recorded. Our admin team will deliver your credentials in this chat shortly.",
            parse_mode="Markdown"
        )
        
        ADMIN_ID = os.getenv("ADMIN_ID")
        if ADMIN_ID:
            alert = (
                "🚨 *AUTOMATED PAYMENT RECEIVED (CRYPTO BOT)!* 🚨\n\n"
                f"👤 *Customer:* {username} (ID: `{user.id}`)\n"
                f"📦 *Quantity:* {qty} Account(s)\n"
                f"💰 *Amount Paid:* ${total_usd:.2f} USD\n"
                f"🧾 *Invoice ID:* `{invoice_id}`\n\n"
                f"👉 DM User: [{user.first_name}](tg://user?id={user.id})"
            )
            await context.bot.send_message(chat_id=int(ADMIN_ID), text=alert, parse_mode="Markdown")
            
        return ConversationHandler.END
    else:
        await query.answer("⏳ Payment not detected yet. Complete the payment in @CryptoBot first!", show_alert=True)
        return CRYPTOBOT_FLOW

# --- OPTION B: MANUAL WALLET PAYMENT FLOW ---

async def manual_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    total_usd = context.user_data.get("total_usd", UNIT_PRICE)
    
    text = (
        f"⚡ *Manual Direct Wallet Payment*\n\n"
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
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    username = f"@{user.username}" if user.username else "No Username"
    qty = context.user_data.get("quantity", 1)
    total_usd = context.user_data.get("total_usd", UNIT_PRICE)
    
    await query.edit_message_text(
        "🎉 *Manual Payment Notification Submitted!*\n\n"
        "Our admin team has been notified. Once confirmed on the blockchain, your account credentials "
        "will be delivered right here in this chat.",
        parse_mode="Markdown"
    )
    
    ADMIN_ID = os.getenv("ADMIN_ID")
    if ADMIN_ID:
        admin_alert_text = (
            "🚨 *NEW MANUAL PAYMENT ALERT!* 🚨\n\n"
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
            SELECT_METHOD: [
                CallbackQueryHandler(cryptobot_flow, pattern="^method_cryptobot$"),
                CallbackQueryHandler(manual_flow, pattern="^method_manual$")
            ],
            CRYPTOBOT_FLOW: [CallbackQueryHandler(check_crypto_status, pattern="^check_crypto_status$")],
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

    print("🤖 FXReplay Bot Online...")
    app.run_polling()

if __name__ == "__main__":
    main()
