import logging
from functools import lru_cache

from aiogram.types import Message
from aiogram.dispatcher import FSMContext

import database as db
from messages import all_texts

from .settings import ask_lang


ru_messages = []
uz_messages = []
en_messages = []

for some_text in all_texts.values():
    ru_messages.append(some_text.get("ru"))
    uz_messages.append(some_text.get("uz"))
    en_messages.append(some_text.get("en"))


@lru_cache
def string_in_messages(string):
    if string in ru_messages:
        return "ru"
    if string in uz_messages:
        return "uz"
    if string in en_messages:
        return "en"


async def get_lang_for(last_arg, context):
    lang = ""
    if context:
        async with context.proxy() as data:
            if data.get("lang"):
                lang = data.get("lang", "uz")

    if (not lang) and isinstance(last_arg, Message):
        lang = string_in_messages(last_arg.text)

    if not lang:
        user_id = last_arg.from_user.id
        lang = await db.get_user_language(user_id)

    return lang


def has_lang(func):
    async def wrapped(*args, **kwargs):
        lang = ""
        last_arg = args[-1]  # Some query or message
        context: FSMContext = kwargs.get("state")  # FSMContext

        lang = await get_lang_for(last_arg, context)

        if lang:
            if context:
                async with context.proxy() as data:
                    data["lang"] = lang
            return await func(lang, *args, **kwargs)
        else:
            await ask_lang(last_arg)

    return wrapped


def has_bearer(func):
    async def wrapped(*args, **kwargs):
        last_arg = args[-1]
        user_id = last_arg.from_user.id

        bearer = await db.get_token(user_id)

        if not bearer:
            await ask_lang(last_arg)
            return
        return await func(bearer, *args, **kwargs)

    return wrapped


async def set_up_keyboard_paginator(lang, elems, keyboard, state):
    async with state.proxy() as data:
        data["page"] = 0
        data["keyboard"] = keyboard
        data["keyboard_args"] = lang, elems
        if not len(elems) > 12:
            return
        return 0


def correct_amount(amount_text: str):
    if not amount_text.isdigit():
        return False
    return True


def get_balance(data):
    response = data['data'][0]['response']
    
    balance_keys = ['saldo', 'balance']
    
    for info in response:
        if info['key'] in balance_keys:
            return info['value']
    return 0


def get_amount(data):
    response = data['data'][0]['response']
    
    amount_keys = ['pay_amount', 'payment_amount']
    
    for info in response:
        if info['key'] in amount_keys:
            return info['value']
    return 0
