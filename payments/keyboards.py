import logging
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from messages import (
    back_button,
    prev_page_button,
    next_page_button,
    mobile_number_payment,
    confirm_button,
    cancel_button,
)


def amount_keyboard(lang, service):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Min...Max')
    markup.add(
        KeyboardButton(f"{service['minAmount']}"),
        KeyboardButton(f"{service['maxAmount']}")
    )
    markup.add(
        KeyboardButton(cancel_button[lang])
    )
    return markup


def inline_markup(elems, markup: InlineKeyboardMarkup, page=0, lang="en"):
    counter = 0
    if len(elems) <= 6:
        while counter < len(elems):
            id, title = elems[counter]
            counter += 1
            markup.add(InlineKeyboardButton(str(title), callback_data=str(id)))

        return markup

    if len(elems) <= 12:
        pairs = len(elems) - 6
        counter = 0
        while counter < len(elems):
            id, title = elems[counter]
            counter += 1
            buttons = [InlineKeyboardButton(title, callback_data=str(id))]
            if pairs:
                pairs -= 1
                id, title = elems[counter]
                counter += 1
                buttons.append(InlineKeyboardButton(title, callback_data=str(id)))
            markup.add(*buttons)
        return markup

    if page is None:
        page = 0

    first = 10 * page
    last = 10 * (page + 1)
    last = last if last < len(elems) else len(elems)
    counter = first
    while counter < last:
        buttons = []

        id, title = elems[counter]
        counter += 1
        buttons.append(InlineKeyboardButton(title, callback_data=str(id)))  # First

        if counter < last:
            id, title = elems[counter]
            counter += 1
            buttons.append(InlineKeyboardButton(title, callback_data=str(id)))  # Second

        markup.add(*buttons)

    control_buttons = []
    if page != 0:
        control_buttons.append(
            InlineKeyboardButton(prev_page_button[lang], callback_data="prev_page")
        )
    # logging.info(f'len: {len(elems)}, {page=}')
    if page != (len(elems) // 10):
        control_buttons.append(
            InlineKeyboardButton(next_page_button[lang], callback_data="next_page")
        )

    markup.add(*control_buttons)
    return markup


def payment_categories_keyboard(lang, categories, back="back", page=None):
    markup = InlineKeyboardMarkup()
    elems = [(category["id"], category["title"][lang]) for category in categories]
    elems[0] = (
        (elems[0][0], mobile_number_payment[lang]) if elems[0][0] == 1 else elems[0]
    )
    markup = inline_markup(elems, markup, page=page, lang=lang)
    markup.add(InlineKeyboardButton(back_button[lang], callback_data=back))
    return markup


def category_providers(lang, providers, page=None):
    markup = InlineKeyboardMarkup()
    elems = [(provider["id"], provider["title_short"]) for provider in providers]
    markup = inline_markup(elems, markup, page=page, lang=lang)
    markup.add(InlineKeyboardButton(back_button[lang], callback_data="back"))
    return markup


def services_keyboard(lang, services):
    markup = InlineKeyboardMarkup()
    markup.add(
        *[
            InlineKeyboardButton(
                service["title"][lang], callback_data=f"{service['id']}"
            )
            for service in services
        ]
    )
    markup.add(InlineKeyboardButton(back_button[lang], callback_data="back"))
    return markup


def confirmation_keyboard(lang):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(confirm_button[lang], callback_data="confirm"),
        InlineKeyboardButton(cancel_button[lang], callback_data="cancel"),
    )
    return markup


def cards_keyboard(lang, cards, page=None):
    markup = InlineKeyboardMarkup()
    elems = [(card["token"], f"💳{card['name']}: {card['mask']}") for card in cards]
    markup = inline_markup(elems, markup, page=page, lang=lang)
    return markup
