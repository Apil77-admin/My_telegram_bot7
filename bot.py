import os
import random
import sqlite3
import string
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

TOKEN = os.environ.get("8064307351:AAG7KtS81OJ4GxlszjRxDmwwhRto7Yyb9-M")
ADMIN_ID = 7914434174


conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    details TEXT,
    tracking_code TEXT
)
""")
conn.commit()

SHARE_THOUGHT, ORDER_WORK, TRACK_ORDER = range(3)

main_keyboard = [
    ["دریافت اثر فاخر"],
    ["اشتراک افکار"],
    ["ارتباط با ادمین"],
    ["بیوگرافی رندوم"],
    ["سفارش کار به ادمین"],
    ["پیگیری سفارشات"],
]

works = {
    "اثر 1": "متن اثر 1",
    "اثر 2": "متن اثر 2",
}

bios = [
    "بیوگرافی شماره 1",
    "بیوگرافی شماره 2",
    "بیوگرافی شماره 3",
]

def generate_tracking_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("به ربات خوش آمدید 👋", reply_markup=reply_markup)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "دریافت اثر فاخر":
        work_buttons = [[w] for w in works.keys()]
        work_buttons.append(["بازگشت"])
        reply_markup = ReplyKeyboardMarkup(work_buttons, resize_keyboard=True)
        await update.message.reply_text("کدام اثر را میخواهید؟", reply_markup=reply_markup)

    elif text in works:
        await update.message.reply_text(works[text])

    elif text == "اشتراک افکار":
        await update.message.reply_text("افکارت را ارسال کن:", reply_markup=ReplyKeyboardRemove())
        return SHARE_THOUGHT

    elif text == "ارتباط با ادمین":
        await update.message.reply_text("ادمین پاسخگوی شماست:\n@admin_username")

    elif text == "بیوگرافی رندوم":
        bio = random.choice(bios)
        await update.message.reply_text(f"{bio}\n\nاز خواندن لذت ببرید ✨")

    elif text == "سفارش کار به ادمین":
        await update.message.reply_text("جزئیات کار را ارسال کن:", reply_markup=ReplyKeyboardRemove())
        return ORDER_WORK

    elif text == "پیگیری سفارشات":
        await update.message.reply_text("کد پیگیری را ارسال کن:", reply_markup=ReplyKeyboardRemove())
        return TRACK_ORDER

    elif text == "بازگشت":
        reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        await update.message.reply_text("بازگشت به منو اصلی", reply_markup=reply_markup)

    return ConversationHandler.END

async def share_thought(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 اشتراک فکر جدید\n\nاز: @{user.username}\nID: {user.id}\n\n{update.message.text}"
    )
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("ممنون 🌹", reply_markup=reply_markup)
    return ConversationHandler.END

async def order_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    tracking_code = generate_tracking_code()

    cursor.execute(
        "INSERT INTO orders (user_id, username, details, tracking_code) VALUES (?, ?, ?, ?)",
        (user.id, user.username, update.message.text, tracking_code)
    )
    conn.commit()

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🛒 سفارش جدید\n\nاز: @{user.username}\nID: {user.id}\n\nجزئیات:\n{update.message.text}\n\nکد پیگیری: {tracking_code}"
    )

    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ سفارش ثبت شد\n\nکد پیگیری شما:\n{tracking_code}\n\nاین کد را نگه دارید.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def track_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text

    cursor.execute("SELECT details FROM orders WHERE tracking_code=?", (code,))
    result = cursor.fetchone()

    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

    if result:
        await update.message.reply_text(
            f"📦 سفارش پیدا شد:\n\n{result[0]}\n\nدر حال بررسی توسط ادمین.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "❌ کد یافت نشد.",
            reply_markup=reply_markup
        )

    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
    states={
        SHARE_THOUGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, share_thought)],
        ORDER_WORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_work)],
        TRACK_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_order)],
    },
    fallbacks=[CommandHandler("start", start)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)

app.run_polling()
