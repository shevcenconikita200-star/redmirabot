import os
import sqlite3
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = os.environ["WEBAPP_URL"]  # HTTPS URL of hosted index.html
IOS_URL = os.environ.get("IOS_URL", "https://example.com")
ANDROID_APK_URL = os.environ.get("ANDROID_APK_URL", "https://example.com/redmira.apk")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

TZ = ZoneInfo("Europe/Chisinau")
RELEASE = datetime(2026, 11, 27, 17, 55, 55, tzinfo=TZ)
DB = "redmira_users.sqlite3"

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger("redmira-bot")


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    return conn


def add_user(chat_id: int):
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO users(chat_id) VALUES (?)", (chat_id,))


def get_users():
    with db() as conn:
        return [r[0] for r in conn.execute("SELECT chat_id FROM users").fetchall()]


def is_release_sent():
    with db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='release_sent'").fetchone()
        return bool(row and row[0] == "1")


def set_release_sent():
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES ('release_sent', '1')"
        )


def release_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🍎 iPhone — открыть сайт", url=IOS_URL),
        InlineKeyboardButton("🤖 Android — скачать APK", url=ANDROID_APK_URL),
    ]])


async def send_release_to_all(app: Application):
    if is_release_sent():
        return
    for chat_id in get_users():
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text="🚀 <b>REDMIRA УЖЕ ВЫШЛА!</b>\n\nВыбирай свою платформу:",
                parse_mode="HTML",
                reply_markup=release_keyboard()
            )
        except Exception:
            log.exception("Не удалось отправить релизное сообщение в чат %s", chat_id)
    set_release_sent()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)

    now = datetime.now(TZ)
    if now >= RELEASE:
        await update.message.reply_text(
            "🚀 REDMIRA УЖЕ ВЫШЛА!\n\nВыбирай свою платформу:",
            reply_markup=release_keyboard()
        )
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "⏳ Открыть обратный отсчёт",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]])
    await update.message.reply_text(
        "🟢 <b>REDMIRA — OFFICIAL</b>\n\n"
        "Обратный отсчёт до выхода уже запущен!\n"
        "Нажми кнопку ниже, чтобы увидеть дни, часы, минуты и секунды.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def release_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return
    now = datetime.now(TZ)
    remaining = RELEASE - now
    if remaining.total_seconds() <= 0:
        await update.message.reply_text("Время релиза уже наступило.")
    else:
        total = int(remaining.total_seconds())
        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        await update.message.reply_text(
            f"Релиз: 27.11.2026 17:55:55 (Кишинёв)\n"
            f"Осталось: {days} дн. {hours} ч. {minutes} мин. {seconds} сек."
        )


async def scheduled_release(context: ContextTypes.DEFAULT_TYPE):
    await send_release_to_all(context.application)


async def post_init(app: Application):
    now = datetime.now(TZ)
    if now >= RELEASE:
        await send_release_to_all(app)
    else:
        app.job_queue.run_once(
            scheduled_release,
            when=(RELEASE - now).total_seconds(),
            name="redmira-release"
        )
        log.info("Релиз запланирован на %s", RELEASE.isoformat())


def main():
    if not WEBAPP_URL.startswith("https://"):
        raise ValueError("WEBAPP_URL должен быть HTTPS-адресом")
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("release", release_command))
    app.run_polling()


if __name__ == "__main__":
    main()
