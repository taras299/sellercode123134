import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import StateFilter
from aiocryptopay import AioCryptoPay, Networks
import database as db
import requests
import random
import string

API_TOKEN = 'botfather'
CRYPTO_PAY_API_KEY = 'cryptopay'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

crypto = AioCryptoPay(token=CRYPTO_PAY_API_KEY, network=Networks.MAIN_NET)

class TopUpState(StatesGroup):
    amount = State()
    invoice_id = State()

db.init_db()

@dp.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    db.add_user(message.from_user.id)
    kb = [
        [
            KeyboardButton(text="Меню"),
            KeyboardButton(text="Профиль")
        ],
        [
            KeyboardButton(text="Инфо")
        ]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Привет! Используй снизу кнопки!", reply_markup=keyboard)

@dp.message(lambda message: message.text == 'Меню')
async def show_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить номер", callback_data="buy_number")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)

@dp.message(lambda message: message.text == 'Профиль')
async def show_profile(message: types.Message):
    user = db.get_user(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить баланс", callback_data="topup_balance")],
        [InlineKeyboardButton(text="Инфо", callback_data="info")],
        [InlineKeyboardButton(text="Вернуться к меню", callback_data="back_to_menu")]
    ])
    await message.answer(f"Баланс: {user[2]}\nID: {message.from_user.id}", reply_markup=keyboard)

@dp.message(lambda message: message.text == 'Инфо')
async def show_info(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тех. Поддержка", url="https://t.me/shavermasupppp")],
        [InlineKeyboardButton(text="Канал", url="https://t.me/shavermasup")],
        [InlineKeyboardButton(text="Правила", callback_data="rules")]
    ])
    await message.answer("Вот актуальные данные:", reply_markup=keyboard)

@dp.callback_query(lambda callback_query: callback_query.data == 'buy_number')
async def process_buy_number(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥Whatsapp", callback_data="buy_whatsapp")],
        [InlineKeyboardButton(text="🔥Olx", callback_data="buy_olx")],
        [InlineKeyboardButton(text="🗳Telegram", callback_data="buy_telegram")],
        [InlineKeyboardButton(text="Вернуться к меню", callback_data="back_to_main_menu")]
    ])
    await callback_query.answer()
    await callback_query.message.answer(
        "Выберите сервис для покупки номера:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda callback_query: callback_query.data.startswith('buy_'))
async def process_buy_service(callback_query: types.CallbackQuery):
    service = callback_query.data.split('_')[1]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить номер", callback_data=f"buy_confirm_{service}"),
         InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")]
    ])
    await callback_query.answer()
    await callback_query.message.answer(
        f"Название товара: Виртуальный номер\n"
        f"Сервис: {service.capitalize()}\n"
        f"Цена: 100р\n"
        f"Описание: Соси хули.\n\n"
        f"Выберите действие:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda callback_query: callback_query.data == 'profile')
async def process_profile(callback_query: types.CallbackQuery):
    user = db.get_user(callback_query.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить баланс", callback_data="topup_balance")],
        [InlineKeyboardButton(text="Инфо", callback_data="info")],
        [InlineKeyboardButton(text="Вернуться к меню", callback_data="back_to_main_menu")]
    ])
    await callback_query.answer()
    await callback_query.message.answer(f"Баланс: {user[2]}\nID: {callback_query.from_user.id}", reply_markup=keyboard)

@dp.callback_query(lambda callback_query: callback_query.data == 'topup_balance')
async def process_topup_balance(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="КриптоБот", callback_data="topup_crypto")],
        [InlineKeyboardButton(text="Рубли", callback_data="topup_rubles")]
    ])
    await callback_query.answer()
    await callback_query.message.answer("Через что хотите?", reply_markup=keyboard)

@dp.callback_query(lambda callback_query: callback_query.data == 'info')
async def process_info(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тех. Поддержка", url="https://t.me/shavermasupppp")],
        [InlineKeyboardButton(text="Канал", url="https://t.me/shavermasup")],
        [InlineKeyboardButton(text="Правила", callback_data="rules")]
    ])
    await callback_query.answer()
    await callback_query.message.answer("Вот актуальные данные:", reply_markup=keyboard)

@dp.callback_query(lambda callback_query: callback_query.data == 'rules')
async def process_rules(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("правила.")

@dp.message(Command(commands=['balance']))
async def set_balance(message: types.Message):
    if is_admin(message.from_user.id):
        parts = message.text.split()
        if len(parts) == 3:
            user_id = int(parts[1])
            amount = float(parts[2])
            db.update_balance(user_id, amount)
            await message.answer("Баланс обновлен.")
        else:
            await message.answer("Использование: /balance [user_id] [amount]")

@dp.message(Command(commands=['ban']))
async def ban_user(message: types.Message):
    if is_admin(message.from_user.id):
        parts = message.text.split()
        if len(parts) == 2:
            user_id = int(parts[1])
            db.ban_user(user_id)
            await message.answer("Пользователь забанен.")
        else:
            await message.answer("Использование: /ban [user_id]")

@dp.message(Command(commands=['unban']))
async def unban_user(message: types.Message):
    if is_admin(message.from_user.id):
        parts = message.text.split()
        if len(parts) == 2:
            user_id = int(parts[1])
            db.unban_user(user_id)
            await message.answer("Пользователь разбанен.")
        else:
            await message.answer("Использование: /unban [user_id]")

@dp.message(Command(commands=['createpromo']))
async def create_promo(message: types.Message):
    if is_admin(message.from_user.id):
        parts = message.text.split()
        if len(parts) == 3:
            uses = int(parts[1])
            amount = float(parts[2])
            promo_code = generate_x_code()
            db.create_promo(promo_code, uses, amount)
            await message.answer(f"Промокод создан: {promo_code}")
        else:
            await message.answer("Использование: /createpromo [uses] [amount]")

@dp.message(Command(commands=['lusers']))
async def list_users(message: types.Message):
    if is_admin(message.from_user.id):
        users = db.list_users()
        msg = "\n".join([f"{user[1]}: {user[2]}" for user in users])
        await message.answer(msg)

@dp.message(Command(commands=['news']))
async def send_news(message: types.Message):
    if is_admin(message.from_user.id):
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2:
            news_text = parts[1]
            users = db.list_users()
            for user in users:
                await bot.send_message(user[1], news_text)
            await message.answer("Новость отправлена.")
        else:
            await message.answer("Использование: /news [message]")

@dp.callback_query(lambda callback_query: callback_query.data == 'topup_crypto')
async def process_topup_crypto(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer("Введите сумму в рублях")
    await state.set_state(TopUpState.amount)

@dp.message(StateFilter(TopUpState.amount))
async def handle_topup_amount(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        try:
            amount_rub = float(message.text)
            logging.info(f"Сумма в рублях: {amount_rub}")
            url = 'https://api.exchangerate-api.com/v4/latest/RUB'
            response = requests.get(url)
            rates = response.json().get('rates')
            rub_to_usd_rate = rates.get('USD')
            logging.info(f"Курс RUB к USD: {rub_to_usd_rate}")
            amount_usd = amount_rub * rub_to_usd_rate
            logging.info(f"Сумма в USD: {amount_usd}")

            invoice = await crypto.create_invoice(asset='USDT', amount=amount_usd, description='Пополнение баланса')
            logging.info(f"Ссылка на оплату инвойса: {invoice.bot_invoice_url}")

            await state.update_data(invoice_id=invoice.invoice_id, amount_rub=amount_rub)
            logging.info(f"Сохраненный идентификатор инвойса: {invoice.invoice_id}")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Проверить оплату", callback_data="check_payment")],
                [InlineKeyboardButton(text="Отменить", callback_data="cancel_payment")]
            ])
            
            await bot.send_message(message.from_user.id, f"Оплатите счет: {invoice.bot_invoice_url}", reply_markup=keyboard)
            await state.set_state(TopUpState.invoice_id)
        except Exception as e:
            logging.error(f"Ошибка при обработке суммы пополнения: {e}")
            await message.reply("Произошла ошибка при обработке суммы пополнения. Попробуйте еще раз.")
            await state.clear()
    else:
        await message.reply("Пожалуйста, введите корректную сумму в рублях.")

@dp.callback_query(lambda callback_query: callback_query.data == 'check_payment')
async def check_payment(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    invoice_id = data.get('invoice_id')
    amount_rub = data.get('amount_rub')
    
    if not invoice_id:
        await callback_query.message.answer("Ошибка: идентификатор инвойса не найден.")
        return

    try:
        invoices = await crypto.get_invoices(invoice_ids=[invoice_id])
        if invoices and len(invoices) > 0:
            invoice = invoices[0]
            if invoice.status == 'paid':
                user = db.get_user(callback_query.from_user.id)
                db.update_balance(callback_query.from_user.id, user[2] + amount_rub)
                await callback_query.message.answer(f"Оплата подтверждена. Ваш баланс пополнен на {amount_rub} рублей.")
                await state.clear()
            else:
                await callback_query.message.answer("Оплата не подтверждена. Пожалуйста, попробуйте позже.")
        else:
            logging.error(f"Получен пустой список инвойсов для ID: {invoice_id}")
            await callback_query.message.answer("Произошла ошибка при проверке оплаты. Попробуйте еще раз.")
    except Exception as e:
        logging.error(f"Ошибка при проверке оплаты: {e}")
        await callback_query.message.answer("Произошла ошибка при проверке оплаты. Попробуйте еще раз.")

@dp.callback_query(lambda callback_query: callback_query.data == 'cancel_payment')
async def cancel_payment(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    invoice_id = data.get('invoice_id')
    
    if not invoice_id:
        await callback_query.message.answer("Ошибка: идентификатор инвойса не найден.")
        return

    try:
        await crypto.delete_invoice(invoice_id=invoice_id)
        await callback_query.message.answer("Оплата отменена.")
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка при отмене оплаты: {e}")
        await callback_query.message.answer("Произошла ошибка при отмене оплаты. Попробуйте еще раз.")

def generate_x_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def is_admin(user_id):
    admin_ids = [6497382050]  
    return user_id in admin_ids

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
