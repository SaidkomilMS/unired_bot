from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from messages import (
    cancel_button,
    start_payments_button,
    start_transactions_button,
    start_settings_button,
    main_menu_placeholder,
    balance_button,
    currencies_button,
    my_cards_button,
    feedback_button,
    about_us_button,
    extra_actions_button,
    back_button,
)


languages_keyboard = InlineKeyboardMarkup()
languages_keyboard.add(
    InlineKeyboardButton("🇺🇿 O'zbek", callback_data="uz"),
    InlineKeyboardButton("🇷🇺 Русский", callback_data="ru"),
    InlineKeyboardButton("🇬🇧 English", callback_data="en"),
)


def cancel_keyboard(lang):
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, selective=True
    )
    markup.add(cancel_button[lang])
    return markup


def main_menu(lang):
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=main_menu_placeholder[lang],
        selective=True,
    )
    markup.add(balance_button[lang], currencies_button[lang])
    markup.add(start_payments_button[lang])
    markup.add(start_transactions_button[lang])
    markup.add(my_cards_button[lang], start_settings_button[lang])
    markup.add(extra_actions_button[lang], about_us_button[lang], feedback_button[lang])
    return markup


def back_keyboard(lang):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(back_button[lang], callback_data="back"))
    return markup
