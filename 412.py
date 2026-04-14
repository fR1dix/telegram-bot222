import asyncio
import re
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("8703221575:AAFV6g29JCxG5Q--u0Ca5P7seC0T5IIsZn0")
ADMIN_ID = 915613103

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_state = {}
user_data = {}
history = {}
last_click = {}

def can_click(user_id):
    now = time.time()
    if user_id in last_click and now - last_click[user_id] < 0.7:
        return False
    last_click[user_id] = now
    return True

def menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📊 Детальний прорахунок")],
            [types.KeyboardButton(text="🧮 Калькулятор склопакета")],
            [types.KeyboardButton(text="🪟 Жалюзі")],
            [types.KeyboardButton(text="📂 Мої розрахунки")],
            [types.KeyboardButton(text="🔧 Замір")],
            [types.KeyboardButton(text="❓ Питання")]
        ],
        resize_keyboard=True
    )

async def send_request(message: types.Message, type_text: str):
    user = message.from_user
    username = f"@{user.username}" if user.username else "❌"
    name = f"{user.first_name or ''}"
    data = user_data.get(user.id, {})
    phone = data.get("phone", "❌")

    await bot.send_message(
        ADMIN_ID,
        f"📥 НОВА ЗАЯВКА\n\n"
        f"👤 {name}\n"
        f"🔗 {username}\n"
        f"🆔 {user.id}\n"
        f"📞 {phone}\n\n"
        f"📌 {type_text}\n\n"
        f"{data}"
    )

@dp.message(Command("start"))
async def start(message: types.Message):
    user_state.pop(message.from_user.id, None)
    await message.answer("👋 Вітаємо!", reply_markup=menu())

@dp.message()
async def handler(message: types.Message):
    user_id = message.from_user.id
    text = (message.text or "").strip().lower()

    if not can_click(user_id):
        return

    state = user_state.get(user_id)

    if text == "📊 детальний прорахунок":
        user_state[user_id] = "detail"
        user_data[user_id] = {}
        await message.answer("📝 Напишіть всі параметри:")
        return

    if text == "❓ питання":
        user_state[user_id] = "question"
        user_data[user_id] = {}
        await message.answer("✍️ Напишіть ваше питання:")
        return

    if text == "🔧 замір":
        user_state[user_id] = "zamir_city"
        user_data[user_id] = {}
        await message.answer("🏙 Місто:")
        return

    if text == "🧮 калькулятор склопакета":
        user_state[user_id] = "type"
        user_data[user_id] = {}
        await message.answer("Тип: звичайний / енерго")
        return

    if text == "🪟 жалюзі":
        user_state[user_id] = "jal_phone"
        user_data[user_id] = {}
        await message.answer("📞 Вкажіть номер:")
        return

    if text == "📂 мої розрахунки":
        h = history.get(user_id, [])
        if not h:
            await message.answer("❌ Немає розрахунків")
        else:
            await message.answer("\n".join(h))
        return

    if any(w in text for w in ["ціна", "скільки", "вартість", "доставка", "гарантія"]):
        await message.answer("ℹ️ Відповідь знайдено.\nПотрібен менеджер?")
        user_state[user_id] = "ask_manager"
        return

    if state == "ask_manager":
        if any(w in text for w in ["так", "да", "хочу"]):
            user_state[user_id] = "question"
            await message.answer("✍️ Напишіть питання:")
        else:
            await message.answer("👌 Добре", reply_markup=menu())
            user_state.pop(user_id, None)
        return

    if state == "question":
        user_data[user_id] = {"question": message.text}
        user_state[user_id] = "phone"
        await message.answer("📞 Номер:")
        return

    if state == "phone":
        user_data.setdefault(user_id, {})["phone"] = message.text
        await send_request(message, "❓ Питання")
        await message.answer("✅ Менеджер зв’яжеться", reply_markup=menu())
        user_state.pop(user_id, None)
        return

    if state == "zamir_city":
        user_data.setdefault(user_id, {})["city"] = message.text
        user_state[user_id] = "zamir_name"
        await message.answer("👤 Ім'я:")
        return

    if state == "zamir_name":
        user_data.setdefault(user_id, {})["name"] = message.text
        user_state[user_id] = "zamir_address"
        await message.answer("📍 Адреса:")
        return

    if state == "zamir_address":
        user_data.setdefault(user_id, {})["address"] = message.text
        user_state[user_id] = "zamir_phone"
        await message.answer("📞 Телефон:")
        return

    if state == "zamir_phone":
        user_data.setdefault(user_id, {})["phone"] = message.text
        await send_request(message, "🔧 Замір")
        await message.answer("✅ Менеджер зв’яжеться", reply_markup=menu())
        user_state.pop(user_id, None)
        return

    if state == "type":
        user_data.setdefault(user_id, {})["type"] = text
        user_state[user_id] = "thick"
        await message.answer("Товщина: 24 або 32")
        return

    if state == "thick":
        user_data.setdefault(user_id, {})["thick"] = text
        user_state[user_id] = "size"
        await message.answer("Розмір: 1200x1400")
        return

    if state == "size":
        s = re.findall(r"\d+", text)
        if len(s) < 2:
            await message.answer("Будь ласка, введіть розмір у форматі 1200x1400")
            return

        w = int(s[0]) / 1000
        h = int(s[1]) / 1000

        if "24" in user_data[user_id].get("thick", ""):
            price = 2050 if "енерго" in user_data[user_id].get("type", "") else 1850
        else:
            price = 2900 if "енерго" in user_data[user_id].get("type", "") else 2700

        total = round(w * h * price)
        history.setdefault(user_id, []).append(f"{total} грн")
        user_data[user_id]["result"] = total
        user_state[user_id] = "calc_phone"

        await message.answer(f"💰 {total} грн\n📞 Номер:")
        return

    if state == "calc_phone":
        user_data.setdefault(user_id, {})["phone"] = message.text
        await send_request(message, f"🧮 Склопакет {user_data[user_id].get('result')} грн")
        await message.answer("✅ Готово", reply_markup=menu())
        user_state.pop(user_id, None)
        return

    if state == "jal_phone":
        user_data[user_id] = {"phone": message.text}
        await send_request(message, "🪟 Жалюзі")
        await message.answer("✅ Менеджер зв’яжеться", reply_markup=menu())
        user_state.pop(user_id, None)
        return

    if state == "detail":
        user_data[user_id] = {"detail": message.text}
        user_state[user_id] = "detail_phone"
        await message.answer("📞 Номер:")
        return

    if state == "detail_phone":
        user_data.setdefault(user_id, {})["phone"] = message.text
        await send_request(message, "📊 Детальний прорахунок")
        await message.answer("✅ Відправлено", reply_markup=menu())
        user_state.pop(user_id, None)
        return

    await message.answer("❗ Оберіть дію", reply_markup=menu())


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())