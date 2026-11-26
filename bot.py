import asyncio
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ============================
# 8877598793:AAFU8vYAftBUluzX6hskL2xcxDcdcVn2QJM
# ============================
BOT_TOKEN = "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН"

# Релиз: 27 ноября 2026, 17:55:55 по Молдове (UTC+2)
RELEASE_AT = datetime.fromisoformat("2026-11-27T17:55:55+02:00")

# Сюда вставь ссылку на iPhone-версию
IPHONE_URL = "https://example.com/redmira"

# APK должен лежать рядом с bot.py
APK_PATH = Path("redmira.apk")

dp = Dispatcher()


def released() -> bool:
    return datetime.now().astimezone() >= RELEASE_AT


def countdown() -> str:
    now = datetime.now().astimezone()
    delta = RELEASE_AT - now
    if delta.total_seconds() <= 0:
        return "🔥 РЕЛИЗ УЖЕ СОСТОЯЛСЯ!"
    total = int(delta.total_seconds())
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"⏳ До релиза: {days} д. {hours:02d}:{minutes:02d}:{seconds:02d}"


def keyboard():
    kb = InlineKeyboardBuilder()
    if released():
        kb.button(text="📱 Android — скачать APK", callback_data="android")
        kb.button(text="🍎 iPhone — скачать", url=IPHONE_URL)
    kb.button(text="🔄 Обновить", callback_data="refresh")
    kb.adjust(1)
    return kb.as_markup()


@dp.message(CommandStart())
async def start(message: Message):
    text = "🔴 RED MIRA\n\n" + countdown()
    if not released():
        text += "\n\n📢 Кнопки скачивания появятся после релиза."
    else:
        text += "\n\n🚀 Скачать приложение:"
    await message.answer(text, reply_markup=keyboard())


@dp.callback_query(F.data == "refresh")
async def refresh(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔴 RED MIRA\n\n" + countdown(),
        reply_markup=keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "android")
async def android(callback: CallbackQuery):
    if not released():
        await callback.answer("Ещё рано 😎", show_alert=True)
        return

    if not APK_PATH.exists():
        await callback.answer("APK пока не загружен.", show_alert=True)
        return

    await callback.message.answer_document(
        FSInputFile(APK_PATH),
        caption="📱 RED MIRA — Android"
    )
    await callback.answer()


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН":
        raise RuntimeError("Вставь токен BotFather в BOT_TOKEN в начале bot.py")

    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
