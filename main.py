import asyncpg

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '6579809280:AAFnbholmlRVY3XWbapn0iRdtrlmjuhZYBE'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
admin_id = 223444075
pool = None


async def create_db_pool():
    return await asyncpg.create_pool(user='postgres', password='Efotod266', database='greys', host='127.0.0.1')


async def on_startup(dp):
    global pool
    pool = await create_db_pool()
    await bot.send_message(chat_id=admin_id, text="Bot has started\n/start")


async def get_username(user_id):
    chat = await bot.get_chat(user_id)
    return chat.full_name


async def add_points(user_id, chat_id, points_to_add):
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE users
            SET points = points + $1
            WHERE user_id = $2 AND chat_id = $3
        ''', points_to_add, user_id, chat_id)


def main_menu_markup():
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("🏠 Личный кабинет", callback_data="personal")
    btn2 = InlineKeyboardButton("📝 Записаться", callback_data="book")
    btn3 = InlineKeyboardButton("👥 Социальные сети", callback_data="socials")
    btn4 = InlineKeyboardButton("📍 Как нас найти", callback_data="location")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup


def get_back_markup():
    markup = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton("Главное меню", callback_data="back")
    markup.add(back_btn)
    return markup


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.message_id
    if pool is not None:
        async with pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, chat_id, points, visits)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, chat_id) DO NOTHING
            ''', user_id, chat_id, 0, 0)
    else:
        print("Pool is not initialized")
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id,
                           "Привет! *Это Grey's Crewz*\nРады видеть тебя, выбери одну из кнопок, что бы продолжить\n\n_Возникли трудности? Напиши менеджеру: @greyscrewz_",
                           reply_markup=main_menu_markup(), parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda c: c.data == 'personal')
async def personal_cabinet(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    if pool is not None:
        async with pool.acquire() as conn:
            response = await conn.fetchrow("SELECT visits, points FROM users WHERE user_id = $1 AND chat_id = $2", user_id, chat_id)
            user = await get_username(user_id)
            visits = response['visits']
            points = response['points']

            if visits != 0:
                await bot.edit_message_text(f"Рады снова видеть, *{user}*!\n У тебя сейчас *{points}* баллов.\nСледующий твой визит будет уже *{visits}* По счету, рады, что ты с нами!",
                                            callback_query.from_user.id,
                                            callback_query.message.message_id,
                                            reply_markup=get_back_markup(),
                                            parse_mode=ParseMode.MARKDOWN)

            if visits == 0 and points == 0:
                await add_points(user_id, chat_id, 200)
                await bot.edit_message_text(
                    f"Привет, *{user}*!\nМы пока еще не встречались, но очень надеемся, что ты скоро заглянешь, поэтому дарим 200 баллов!\nБаланс: {points} баллов",
                    callback_query.from_user.id,
                    callback_query.message.message_id,
                    reply_markup=get_back_markup(),
                    parse_mode=ParseMode.MARKDOWN)

            if visits == 0 and points != 0:
                await bot.edit_message_text(
                    f"Рады снова видеть, *{user}*!\n У тебя сейчас *{points}* баллов.\nПриходи, что бы их потратить!",
                    callback_query.from_user.id,
                    callback_query.message.message_id,
                    reply_markup=get_back_markup(),
                    parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda c: c.data == 'book')
async def book_appointment(callback_query: types.CallbackQuery):
    await bot.edit_message_text("Здесь будет информация о том, как записаться.",
                                callback_query.from_user.id,
                                callback_query.message.message_id,
                                reply_markup=get_back_markup())


@dp.callback_query_handler(lambda c: c.data == 'socials')
async def social_media(callback_query: types.CallbackQuery):
    await bot.edit_message_text("Здесь будет информация о наших социальных сетях.",
                                callback_query.from_user.id,
                                callback_query.message.message_id,
                                reply_markup=get_back_markup())


@dp.callback_query_handler(lambda c: c.data == 'location')
async def find_us(callback_query: types.CallbackQuery):
    await bot.edit_message_text("Здесь будет информация о том, как нас найти.",
                                callback_query.from_user.id,
                                callback_query.message.message_id,
                                reply_markup=get_back_markup())


@dp.callback_query_handler(lambda c: c.data == 'back')
async def go_back(callback_query: types.CallbackQuery):
    await bot.edit_message_text(
        "Привет! *Это Grey's Crewz*\nРады видеть тебя, выбери одну из кнопок, чтобы продолжить\n\n_Возникли трудности? Напиши менеджеру: @greyscrewz_",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=main_menu_markup(),
        parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
