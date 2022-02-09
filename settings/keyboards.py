from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import database as db
from messages import phone_number_placeholder, send_contact_button, cancel_button


async def phone_number_keyboard(lang, add_users_number=False, add_cancel=False, chat_id=None):
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        selective=True,
        one_time_keyboard=True,
        input_field_placeholder=phone_number_placeholder[lang],
    )
    if add_users_number and chat_id is not None:
        phone_number = await db.get_phone_number(chat_id)
        markup.add(KeyboardButton(phone_number))
    if not add_users_number or not await db.user_is_contact(chat_id):
        markup.add(KeyboardButton(send_contact_button[lang], request_contact=True))
    if add_cancel:
        markup.add(KeyboardButton(cancel_button[lang]))
    return markup
