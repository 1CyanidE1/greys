import asyncpg

import datetime
from datetime import timedelta
import calendar
import typing

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# from storage import MemoryStorage

pool = None
location_message_id = {}
date = {
    'month': {},
    'day': {},
}

ru = {
    'January': 'января',
    'February': 'февраля',
    'March': 'марта',
    'April': 'апреля',
    'May': 'мая',
    'June': 'июня',
    'July': 'июля',
    'August': 'августа',
    'September': 'сентября',
    'October': 'октября',
    'November': 'ноября',
    'December': 'декабря'
}

services = {
    "Однотонное покрытие": 90,
    "Покрытие с дизайном на короткие ногти": 120,
    "Покрытие с дизайном на любую длину натуральных ногтей": 120,
    "Наращивание с любым дизайном (до 6)": 180,
    "Коррекция наращивания с любым дизайном (до 6)": 150,
    "Наращивание экстра длинны (от 6)": 240,
    "Наращивание кошачьих когтей (до 6)": 240,
    "Наращивание кошачьих когтей экстра длины (от 6)": 270,
    "Другое": 180
}

services_list = list(services.keys())


async def create_db_pool():
    return await asyncpg.create_pool(user='postgres', password='Efotod266', database='greys', host='127.0.0.1')


async def on_startup(dp):
    global pool
    pool = await create_db_pool()
    await bot.send_message(chat_id=admin_id, text="Bot has started\n/start")


API_TOKEN = '6579809280:AAFnbholmlRVY3XWbapn0iRdtrlmjuhZYBE'

bot = Bot(token=API_TOKEN)
# storage = MemoryStorage()
dp = Dispatcher(bot)
admin_id = 223444075


async def update_user_booking(user_id, book_date, book_time):
    book_date_obj = datetime.datetime.strptime(book_date, "%Y-%m-%d").date()
    book_time_obj = datetime.datetime.strptime(book_time, "%H:%M").time()
    if pool is not None:
        async with pool.acquire() as conn:
            await conn.execute('''
                UPDATE users SET book_status = $1, book_date = $2, book_time = $3 WHERE user_id = $4
            ''', True, book_date_obj, book_time_obj, user_id)


async def get_booked_times(date):
    global pool
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT book_time FROM users WHERE book_date = $1 AND book_status = true", date)
        booked_times = [row['book_time'] for row in rows]
        return booked_times


async def check_active_booking(user_id):
    if pool is not None:
        async with pool.acquire() as conn:
            result = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1 AND book_status = True', user_id)

    return result is not None


async def get_booking_info(user_id):
    if pool is not None:
        async with pool.acquire() as conn:
            result = await conn.fetchrow('SELECT book_date, book_time FROM users WHERE user_id = $1 AND book_status = True',
                                     user_id)

    return result


async def cancel_booking(user_id):
    if pool is not None:
        async with pool.acquire() as conn:
            await conn.execute('''
                UPDATE users SET book_status = $1, book_date = $2, book_time = $3 WHERE user_id = $4
            ''', False, None, None, user_id)


def create_calendar(year=None, month=None):
    markup = InlineKeyboardMarkup()

    today = datetime.date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    month_name = calendar.month_name[month]
    markup.add(InlineKeyboardButton(text=f"{month_name} {year}", callback_data="ignore"))

    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    row = []
    for day in days:
        row.append(InlineKeyboardButton(text=day, callback_data="ignore"))
    markup.row(*row)

    month_days = calendar.monthrange(year, month)[1]
    first_weekday = calendar.monthrange(year, month)[0]

    day_buttons = [InlineKeyboardButton(text=" ", callback_data="ignore") for _ in range(first_weekday)]

    for day in range(1, month_days + 1):

        if datetime.date(year, month, day) <= today:
            button_text = " "
            callback_data = "ignore"
        else:
            button_text = str(day)
            callback_data = f"day-{day}"

        day_buttons.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))

        if len(day_buttons) % 7 == 0 or day == month_days:
            if day == month_days and len(day_buttons) < 7:
                day_buttons.extend(
                    [InlineKeyboardButton(text=" ", callback_data="ignore") for _ in range(7 - len(day_buttons))])
            markup.row(*day_buttons)
            day_buttons = []

    is_current_month = year == today.year and month == today.month
    is_next_month = year == today.year and month == today.month + 1

    prev_button = InlineKeyboardButton(text="⬅️",
                                       callback_data="prev_month") if not is_current_month else InlineKeyboardButton(
        text=" ", callback_data="ignore")
    next_button = InlineKeyboardButton(text="➡️",
                                       callback_data="next_month") if not is_next_month else InlineKeyboardButton(
        text=" ", callback_data="ignore")

    markup.add(prev_button, next_button)
    markup.add(InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back"))

    return markup


# def create_time_slots_keyboard():
#     markup = InlineKeyboardMarkup()
#
#     times = [(hour, minute) for hour in range(11, 20) for minute in [0, 30] if not (hour == 19 and minute == 30)]
#     for i in range(0, len(times), 2):
#         if i + 1 < len(times):
#             button1 = InlineKeyboardButton(text=f"{times[i][0]}:{times[i][1]:02}",
#                                            callback_data=f"time-{times[i][0]}:{times[i][1]:02}")
#             button2 = InlineKeyboardButton(text=f"{times[i + 1][0]}:{times[i + 1][1]:02}",
#                                            callback_data=f"time-{times[i + 1][0]}:{times[i + 1][1]:02}")
#             markup.row(button1, button2)
#         else:
#             button = InlineKeyboardButton(text=f"{times[i][0]}:{times[i][1]:02}",
#                                           callback_data=f"time-{times[i][0]}:{times[i][1]:02}")
#             markup.add(button)
#
#     return markup


async def is_time_slot_available(user_id, time_slot, service):
    duration = services[service]
    end_time = (time_slot[0] * 60 + time_slot[1] + duration) // 60, (time_slot[0] * 60 + time_slot[1] + duration) % 60
    if user_id not in date['month']:
        date_object = datetime.date(year=datetime.datetime.now().year, month=datetime.datetime.now().month,
                                    day=int(date['day'][user_id]))
    else:
        date_object = datetime.date(year=datetime.datetime.now().year, month=int(date['month'][user_id]),
                                    day=int(date['day'][user_id]))

    booked_times = await get_booked_times(date_object)

    booked_time_slots = [(time.hour, time.minute) for time in booked_times]

    for hour, minute in [(h, m) for h in range(time_slot[0], end_time[0] + 1) for m in [0, 30]]:
        if (hour, minute) in booked_time_slots:
            return False
    return True


async def create_time_slots_keyboard(user_id, date, service):
    markup = InlineKeyboardMarkup(row_width=2)

    # Запрашиваем занятые слоты из базы данных
    booked_times = await get_booked_times(date)

    # Преобразование booked_times в удобный список
    booked_time_slots = [tuple(map(int, time.split(":"))) for time in booked_times]

    times = [(h, m) for h in range(11, 19) for m in [0, 30]]

    for hour, minute in times:
        time_slot = (hour, minute)
        if time_slot not in booked_time_slots and await is_time_slot_available(user_id, time_slot, service):
            markup.add(InlineKeyboardButton(text=f"{hour}:{minute:02}", callback_data=f"time-{hour}:{minute}"))

    return markup


def create_service_keyboard():
    markup = InlineKeyboardMarkup()

    for index, service in enumerate(services):
        markup.add(InlineKeyboardButton(text=service, callback_data=f"service-{index}"))

    return markup


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
    back_btn = InlineKeyboardButton("⬅️ Главное меню", callback_data="back")
    markup.add(back_btn)
    return markup


def social_markup():
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("📸 Инстаграм", url="https://instagram.com/greyscrewz/")
    btn2 = InlineKeyboardButton("📘 Канал телеграмм", url="https://t.me/greyscrew/")
    btn3 = InlineKeyboardButton("⬅️ Главное меню", callback_data="back")
    markup.add(btn1, btn2)
    markup.add(btn3)
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
            response = await conn.fetchrow("SELECT visits, points FROM users WHERE user_id = $1 AND chat_id = $2",
                                           user_id, chat_id)
            visits = response['visits']
            points = response['points']

            if visits == 0 and points == 0:
                await add_points(user_id, chat_id, 200)
                user = await get_username(user_id)
                await bot.send_message(chat_id,
                                       f"Привет, *{user}*! *Это Grey's Crewz*\n"
                                       f"Мы пока еще не встречались, но очень надеемся, что ты скоро заглянешь,"
                                       f" поэтому дарим 200 баллов!\n\n"
                                       f"_Возникли трудности? Напиши менеджеру: @greyscrewz_",
                                       reply_markup=main_menu_markup(), parse_mode=ParseMode.MARKDOWN)
                return
    else:
        print("Pool is not initialized")

    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id,
                           "Привет! *Это Grey's Crewz*\n"
                           "Рады видеть тебя, выбери одну из кнопок, чтобы продолжить\n\n"
                           "_Возникли трудности? Напиши менеджеру: @greyscrewz_",
                           reply_markup=main_menu_markup(), parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda c: c.data == 'personal')
async def personal_cabinet(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    booking_info = await get_booking_info(user_id)

    if pool is not None:
        async with pool.acquire() as conn:
            response = await conn.fetchrow("SELECT visits, points FROM users WHERE user_id = $1 AND chat_id = $2",
                                           user_id, chat_id)
            user = await get_username(user_id)
            visits = response['visits']
            points = response['points']

            markup = InlineKeyboardMarkup()
            btn1 = InlineKeyboardButton("❌ Отменить запись", callback_data="cancel_booking")
            back_btn = InlineKeyboardButton("⬅️ Главное меню", callback_data="back")
            markup.add(btn1, back_btn)

            if visits != 0:

                if booking_info:
                    book_date = booking_info['book_date']
                    book_time = booking_info['book_time']

                    await bot.edit_message_text(
                        f"Рады снова видеть, *{user}*!\n"
                        f"У Вас сейчас *{points}* баллов.\n\n"
                        f"Так же, у Вас есть запись на {book_date.strftime('%d')} {ru[book_date.strftime('%B')]} число"
                        f" в {book_time.strftime('%H:%M')} часов.\n"
                        f"Очень ждем!",
                        callback_query.from_user.id,
                        callback_query.message.message_id,
                        reply_markup=markup,
                        parse_mode=ParseMode.MARKDOWN)

                else:
                    await bot.edit_message_text(
                        f"Рады снова видеть, *{user}*!\n"
                        f"У Вас сейчас *{points}* баллов.\n"
                        f"К сожалению, У вас сейчас нет активных записей, "
                        f"но мы Вас очень ждем!",
                        callback_query.from_user.id,
                        callback_query.message.message_id,
                        reply_markup=get_back_markup(),
                        parse_mode=ParseMode.MARKDOWN)

            if visits == 0 and points != 0:

                if booking_info:
                    book_date = booking_info['book_date']
                    book_time = booking_info['book_time']

                    await bot.edit_message_text(
                        f"Рады снова видеть, *{user}*!\n"
                        f"У Вас сейчас *{points}* баллов.\n\n"
                        f"Так же, у Вас есть запись на {book_date.strftime('%d')} {ru[book_date.strftime('%B')]} число"
                        f" в {book_time.strftime('%H:%M')} часов.\n"
                        f"Очень ждем!",
                        callback_query.from_user.id,
                        callback_query.message.message_id,
                        reply_markup=markup,
                        parse_mode=ParseMode.MARKDOWN)

                else:
                    await bot.edit_message_text(
                        f"Рады снова видеть, *{user}*!\n"
                        f"У Вас сейчас *{points}* баллов.\n"
                        f"Приходите, что бы их потратить!",
                        callback_query.from_user.id,
                        callback_query.message.message_id,
                        reply_markup=get_back_markup(),
                        parse_mode=ParseMode.MARKDOWN)

            if visits == 0 and points == 200:

                if booking_info:
                    book_date = booking_info['book_date']
                    book_time = booking_info['book_time']

                    await bot.edit_message_text(
                        f"Добро пожаловать, *{user}*!\n"
                        f"У Вас сейчас *{points}* баллов.\n\n"
                        f"Так же, у Вас есть запись на {book_date.strftime('%d')} {ru[book_date.strftime('%B')]} число"
                        f" в {book_time.strftime('%H:%M')} часов.\n"
                        f"Очень ждем!",
                        callback_query.from_user.id,
                        callback_query.message.message_id,
                        reply_markup=markup,
                        parse_mode=ParseMode.MARKDOWN)

                else:
                    await bot.edit_message_text(
                        f"Добро пожаловать, *{user}*!\n"
                        f"У Вас сейчас *{points}* баллов.\n"
                        f"Приходите, что бы их потратить!",
                        callback_query.from_user.id,
                        callback_query.message.message_id,
                        reply_markup=get_back_markup(),
                        parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda c: c.data == 'cancel_booking')
async def cancel_booking_query(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    booking_info = await get_booking_info(user_id)

    if booking_info:
        book_datetime = datetime.datetime.combine(booking_info['book_date'], booking_info['book_time'])

        time_difference = book_datetime - datetime.datetime.now()

        if time_difference < timedelta(days=1):
            await bot.edit_message_text(
                "К сожалению, отменить запись можно не позднее, чем за 24 часа до начала.",
                callback_query.from_user.id,
                callback_query.message.message_id,
                reply_markup=get_back_markup()
            )
            return

    markup = InlineKeyboardMarkup(row_width=2)

    yes_button = InlineKeyboardButton("✅ Да", callback_data="confirm_cancel")
    no_button = InlineKeyboardButton("❌ Нет", callback_data="back")

    markup.add(yes_button, no_button)

    await bot.edit_message_text(
        "Вы уверены, что хотите отменить запись?",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=markup
    )


@dp.callback_query_handler(lambda c: c.data == 'confirm_cancel')
async def confirm_cancellation(callback_query: types.CallbackQuery):
    await cancel_booking(callback_query.from_user.id)
    await bot.edit_message_text(
        "Запись отменена.",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=get_back_markup()
    )


@dp.callback_query_handler(lambda c: c.data == 'book')
async def book_appointment(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if await check_active_booking(user_id):
        await bot.edit_message_text("У тебя уже есть активная запись!\nУзнать подробнее можешь в личном кабинете.",
                                    callback_query.from_user.id,
                                    callback_query.message.message_id,
                                    reply_markup=get_back_markup())

    else:
        await bot.edit_message_text("Выберите дату.",
                                    callback_query.from_user.id,
                                    callback_query.message.message_id,
                                    reply_markup=create_calendar())


@dp.callback_query_handler(lambda c: c.data == 'prev_month' or c.data == 'next_month')
async def process_month_navigation(callback_query: types.CallbackQuery, state: FSMContext):
    current_data = await state.get_data()

    year = current_data.get('year', datetime.date.today().year)
    month = current_data.get('month', datetime.date.today().month)

    global date

    if callback_query.data == 'prev_month':
        selected_month = current_data.get('month', datetime.date.today().month)
        date['month'][callback_query.from_user.id] = selected_month
        if month == 0:  # Если предыдущий месяц - декабрь предыдущего года
            month = 12
            year -= 1

    elif callback_query.data == 'next_month':
        selected_month = current_data.get('month', datetime.date.today().month) + 1
        date['month'][callback_query.from_user.id] = selected_month
        month += 1
        if month == 13:  # Если следующий месяц - январь следующего года
            month = 1
            year += 1

    # Сохраняем новые месяц и год в состояние
    await state.set_data({'year': year, 'month': month})

    # Обновляем сообщение с календарем
    markup = create_calendar(year, month)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text="Выберите дату:", reply_markup=markup)


# @dp.callback_query_handler(lambda c: c.data.startswith('day-'))
# async def process_day_selection(callback_query: types.CallbackQuery, state: FSMContext):
#     print(callback_query.data)
#     current_day = datetime.datetime.now().date()
#     selected_day = callback_query.data.split('-')[1]
#     user_id = callback_query.from_user.id
#
#     global date
#     date['day'][user_id] = selected_day
#
#     markup = create_time_slots_keyboard()
#     await bot.edit_message_text(chat_id=callback_query.from_user.id,
#                                 message_id=callback_query.message.message_id,
#                                 text=f"Вы выбрали {selected_day} число. Теперь выберите удобное для вас время:",
#                                 reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith('day-'))
async def process_day_selection(callback_query: types.CallbackQuery, state: FSMContext):
    selected_day = callback_query.data.split('-')[1]
    user_id = callback_query.from_user.id

    global date
    date['day'][user_id] = selected_day

    markup = create_service_keyboard()
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=f"Теперь выберите услугу:",
                                reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith('service-'))
async def process_service_selection(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем имя услуги из callback_data
    selected_service_index = int(callback_query.data.split('-')[1])
    selected_service_name = services_list[selected_service_index]

    await state.update_data(selected_service=selected_service_name)

    if selected_service_name == "Другое":
        await bot.send_message(chat_id=callback_query.from_user.id, text="Пожалуйста, опишите, что вы хотите.")
        return

    # Получаем текущую дату или дату, которую вы хотите использовать для бронирования
    current_date = datetime.date.today()  # или другая дата, которую вы решите использовать

    # Получаем клавиатуру временных слотов
    markup = await create_time_slots_keyboard(callback_query.from_user.id, current_date, selected_service_name)

    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=f"Вы выбрали услугу: {selected_service_name}. Теперь выберите удобное для вас "
                                     f"время:",
                                reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith('time-'))
async def process_time_selection(callback_query: types.CallbackQuery, state: FSMContext):
    selected_time = callback_query.data.split('-')[1]
    user_id = callback_query.from_user.id

    global date

    selected_day = date['day'][user_id]
    if date['month']:
        selected_month = date['month'][user_id]

    else:
        current_data = await state.get_data()
        selected_month = selected_month = current_data.get('month', datetime.date.today().month)

    current_data = await state.get_data()
    year = current_data.get('year', datetime.date.today().year)
    month = current_data.get('month', datetime.date.today().month)
    book_date = f"{year}-{selected_month}-{selected_day}"

    # Записываем данные в базу
    await update_user_booking(callback_query.from_user.id, book_date, selected_time)

    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=f"Вы записались на {selected_day}, время {selected_time}. Спасибо!\n"
                                     f"Отслеживать свою запись вы можете в личном кабинете, там же, при необходимости, ее можно отменить.",
                                reply_markup=get_back_markup())


@dp.callback_query_handler(lambda c: c.data == 'socials')
async def social_media(callback_query: types.CallbackQuery):
    await bot.edit_message_text("Наши социальные сети!",
                                callback_query.from_user.id,
                                callback_query.message.message_id,
                                reply_markup=social_markup())


@dp.callback_query_handler(lambda c: c.data == 'location')
async def find_us(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("📸 Видео маршрута от Сенной площади", url="https://instagram.com/greyscrewz/")
    btn2 = InlineKeyboardButton("⬅️ Главное меню", callback_data="back")
    markup.add(btn1)
    markup.add(btn2)
    await bot.edit_message_text("Наш адрес: Санкт-Петербург, Московский проспект, 2/6.\n"
                                "Код домофона - 12",
                                callback_query.from_user.id,
                                callback_query.message.message_id,
                                reply_markup=markup)

    sent_message = await bot.send_location(callback_query.from_user.id, latitude=59.92622, longitude=30.31827)
    location_message_id[user_id] = sent_message.message_id


@dp.callback_query_handler(lambda c: c.data == 'back')
async def go_back(callback_query: types.CallbackQuery):
    global location_message_id
    if location_message_id:
        await bot.delete_message(callback_query.from_user.id, location_message_id[callback_query.from_user.id])
        location_message_id = {}
    await bot.edit_message_text(
        "Привет! *Это Grey's Crewz*\n"
        "Рады видеть тебя, выбери одну из кнопок, чтобы продолжить\n\n"
        "_Возникли трудности? Напиши менеджеру: @greyscrewz_",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=main_menu_markup(),
        parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
