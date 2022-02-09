from datetime import datetime
import logging
import re
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, ContentTypes
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

import database as db
from controller import dp, bot
from messages import (
    ask_phone_number,
    ask_SMS_code,
    wrong_phone_number,
    ask_password,
    wrong_SMS_code,
    wrong_password,
    wrong_email,
    login_success,
    ask_name,
    ask_last_name,
    ask_email,
    ask_new_password,
)
from utils import has_lang
from utils.requests import login, step_one, step_two, register
from keyboards import cancel_keyboard, languages_keyboard, main_menu
from utils.settings import ask_lang

from .states import Register, SignIn
from .keyboards import phone_number_keyboard

languages = {
    "uz": "🇺🇿 O'zbek tili",
    "ru": "🇷🇺 Русский язык",
    "en": "🇬🇧 English language",
}


@dp.message_handler(commands="start", state="*")
async def cmd_start(message: Message, state: FSMContext):
    # db.add_user_old(message.from_user.id)
    await db.add_user(message.from_user.id)
    await ask_lang(message)


@dp.callback_query_handler(state=SignIn.language)
async def save_language(query: CallbackQuery, state: FSMContext):
    lang = query.data
    # db.set_language_old(query.from_user.id, lang)
    await db.set_language(query.from_user.id, lang)
    await query.message.edit_text(
        f"{query.message.html_text}\n\n{languages[lang]}",
        reply_markup=None,
        parse_mode="html",
    )
    async with state.proxy() as data:
        data["lang"] = lang

    await SignIn.next()

    await query.message.answer(
        ask_phone_number[lang], reply_markup=await phone_number_keyboard(lang)
    )


async def handle_phone_number(user_id, phone_number, lang, state, user_is_contact=False):
    # db.set_phone_number(user_id, phone_number)
    await db.set_phone_number(user_id, phone_number, user_is_contact)
    response_data = step_one(phone_number, lang)
    if response_data:
        otp_token, unired_id = response_data["otp"], response_data["id"]
        async with state.proxy() as data:
            data["otp_token"] = otp_token
            data["unired_id"] = unired_id
            data["mobile"] = phone_number
        # db.set_last_otp_token_old(user_id, otp_token)
        # db.set_unired_id_old(user_id, unired_id)
        await db.set_last_otp_token(user_id, otp_token)
        await db.set_unired_id(user_id, unired_id)


@dp.message_handler(content_types=ContentTypes.CONTACT, state=SignIn.phone_number)
@has_lang
async def get_contact(lang, message: Message, state: FSMContext, raw_state):
    phone_number = message.contact.phone_number
    phone_number = phone_number[1:] if '+' in phone_number else phone_number
    await handle_phone_number(message.from_user.id, phone_number, lang, state, True)
    await SignIn.next()
    await message.answer(ask_SMS_code[lang], reply_markup=ReplyKeyboardRemove())


@dp.message_handler(regexp=r"\+?[\d]{12}|[\d]{9}", state=SignIn.phone_number)
@has_lang
async def get_phone_number(
    lang, message: Message, state: FSMContext, raw_state, regexp
):
    phone_number = message.text[1:] if "+" in message.text else message.text
    phone_number = ("998" + phone_number) if len(phone_number) == 9 else phone_number
    await handle_phone_number(message.from_user.id, phone_number, lang, state)
    await SignIn.next()
    await message.answer(ask_SMS_code[lang], reply_markup=ReplyKeyboardRemove())


@dp.message_handler(state=SignIn.phone_number)
@has_lang
async def ask_phone_number_again(lang, message: Message, state: FSMContext, raw_state):
    await message.answer(wrong_phone_number[lang])


@dp.message_handler(regexp=r"\d{5}", state=SignIn.SMScode)
@has_lang
async def get_SMS_code(lang, message: Message, state: FSMContext, raw_state, regexp):
    sms_code = message.text
    async with state.proxy() as data:
        otp_token = data.get("otp_token", "")

    is_registered = step_two(otp_token, sms_code)

    if is_registered is None:
        await message.answer(wrong_SMS_code[lang])
        return

    if is_registered:  # Login else register
        # db.set_user_registered(message.from_user.id)
        await db.set_user_registered(message.from_user.id)
        await SignIn.next()
        await message.answer(ask_password[lang])
    else:
        await Register.name.set()

        await message.answer(ask_name[lang])


@dp.message_handler(state=Register.name)
@has_lang
async def get_name(lang, message: Message, state: FSMContext, raw_state):
    name = message.text

    async with state.proxy() as data:
        data["name"] = name

    await Register.next()
    await message.answer(ask_last_name[lang])


@dp.message_handler(state=Register.last_name)
@has_lang
async def get_last_name(lang, message: Message, state: FSMContext, raw_state):
    last_name = message.text

    async with state.proxy() as data:
        data["last_name"] = last_name

    await Register.next()
    await message.answer(ask_email[lang])


@dp.message_handler(state=Register.email)
@has_lang
async def get_email(lang, message: Message, state: FSMContext, raw_state):
    email = message.text

    pattern = re.compile("[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+")

    if not pattern.match(email):
        await message.answer(wrong_email[lang])
        return

    async with state.proxy() as data:
        data["email"] = email

    await Register.next()
    await message.answer(ask_new_password[lang])


@dp.message_handler(state=Register.password)
@has_lang
async def get_password(lang, message: Message, state: FSMContext, raw_state):
    password = message.text

    pattern = re.compile("[\d]{5}")

    if not pattern.match(password):
        await message.answer(wrong_password[lang])
        return

    async with state.proxy() as data:
        data["password"] = password

    async with state.proxy() as data:
        otp_token = data["otp_token"]
        name = data["name"]
        last_name = data["last_name"]
        mobile = data["mobile"]
        email = data["email"]
    data = register(otp_token, name, last_name, mobile, email, password)
    access_token = data["access_token"]
    expires_at_str = data["expires_at"]
    if expires_at_str:
        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
    else:
        expires_at = datetime.now()

    # db.set_PIN(message.from_user.id, password)
    # db.save_data(message.from_user.id, name, last_name, access_token, expires_at)
    await db.set_password(message.from_user.id, password)
    await db.save_user_info(message.from_user.id, name, last_name, access_token, expires_at)

    await state.finish()
    await message.answer(login_success[lang], reply_markup=main_menu(lang))


@dp.message_handler(state=SignIn.SMScode)
@has_lang
async def get_wrong_SMS(lang, message: Message, state: FSMContext, raw_state):
    await message.answer(wrong_phone_number[lang])


@dp.message_handler(
    lambda mes: mes.text.isdigit() and len(mes.text) == 5, state=SignIn.password
)
@has_lang
async def log_in(lang, message: Message, state: FSMContext, raw_state):
    password = message.text

    async with state.proxy() as data:
        otp_token = data.get("otp_token", "")
    user_info = login(otp_token, password)

    if user_info is None:
        await message.answer(wrong_password[lang])
        return

    # db.set_PIN(message.from_user.id, password)
    await db.set_password(message.from_user.id, password)

    name = user_info.get("name", "")
    last_name = user_info.get("last_name", "")
    access_token = user_info.get("access_token", "")
    expires_at_str = user_info.get("expires_at", "")  # 2022-07-19 16:16:12
    if expires_at_str:
        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
    else:
        expires_at = datetime.now()

    # db.save_data(message.from_user.id, name, last_name, access_token, expires_at)
    await db.save_user_info(message.from_user.id, name, last_name, access_token, expires_at)

    await message.answer(login_success[lang], reply_markup=main_menu(lang))
    await state.finish()
