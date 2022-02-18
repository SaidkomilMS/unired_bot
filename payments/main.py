import logging
from pprint import pprint
import re

from aiogram.types import Message, CallbackQuery, ContentTypes
from aiogram.dispatcher import FSMContext
from settings.keyboards import phone_number_keyboard

from messages import (
    ok_mes,
    ask_category,
    ask_service,
    ask_phone_number,
    ask_amount,
    wrong_amount,
    wrong_phone_number,
    ask_payment_confirmation,
    ask_card_to_pay,
    chosen_card,
    verified_cards_not_found,
    not_enough_money_in_cards,
    main_menu_placeholder
)
from utils import (
    correct_amount,
    has_bearer,
    has_lang,
    requests,
    set_up_keyboard_paginator,
)
from keyboards import cancel_keyboard, back_keyboard, main_menu
from settings.main import dp
from utils.payments import (
    field_type_is,
    get_exact_field,
    get_info_service,
    get_useful_info,
    save_cur_message,
    save_field,
    check_field,
    get_next_field_state,
    set_amount_for_phone_number,
    set_provider_from_phone_number,
)

from .states import MobilePayment, Payment
from .filters import (
    payment_start_filter,
    category_filter,
    category_re,
    provider_filter,
    provider_re,
    service_filter,
    service_re,
)
from .keyboards import (
    amount_keyboard,
    cards_keyboard,
    category_providers,
    inline_keyboard_from_keys,
    payment_categories_keyboard,
    services_keyboard,
    confirmation_keyboard,
)
from .back_buttons import back_to_all_categories, cancel_all


card_tokens = {}
card_types = {}
fields_info = {}


@dp.message_handler(payment_start_filter)
@has_bearer
@has_lang
async def start_payment(
    lang, bearer_token, message: Message, state: FSMContext, raw_state
):
    await Payment.category.set()
    await message.reply(ok_mes[lang], reply_markup=cancel_keyboard(lang))

    categories = requests.get_payment_categories(bearer_token)
    page = (
        await set_up_keyboard_paginator(
            lang, categories, payment_categories_keyboard, state
        )
        or None
    )

    await save_cur_message(
        await message.answer(
            ask_category[lang],
            reply_markup=payment_categories_keyboard(lang, categories, page=page),
        ),
        state,
    )


@dp.callback_query_handler(category_filter, state=Payment.category)
@has_bearer
@has_lang
async def get_category(
    lang, bearer_token, query: CallbackQuery, state: FSMContext, raw_state
):
    category_id = int(category_re.findall(query.data)[0])

    if category_id == 20:
        categories = requests.get_kommunal_categories(bearer_token)
        await query.message.edit_reply_markup(
            payment_categories_keyboard(lang, categories, back="back_to_all")
        )
        return

    category_data = requests.get_category_providers(category_id, bearer_token)
    providers = category_data["data"][0]["providers"]

    page = (
        await set_up_keyboard_paginator(lang, providers, category_providers, state)
        or None
    )

    async with state.proxy() as data:
        data["category_data"] = category_data
        data["category_id"] = category_id
        data["providers"] = providers

    if category_id == 1:
        await MobilePayment.first()
        await query.message.answer(
            ask_phone_number[lang],
            reply_markup=await phone_number_keyboard(
                lang, add_users_number=True, add_cancel=True, chat_id=query.from_user.id
            ),
        )
        await query.message.delete()
        return

    await query.answer()
    await query.message.edit_text(
        ask_service[lang], reply_markup=category_providers(lang, providers, page=page)
    )
    await Payment.next()


async def ask_first_field(lang, service, query: CallbackQuery, state):
    fields = service["fields"]
    fields_state = 0

    fields_state = get_next_field_state(fields_state, fields)

    if not len(fields) > fields_state:
        return

    async with state.proxy() as data:
        data["service"] = service
        data["fields"] = fields
        data["fields_state"] = fields_state

    await Payment.fields.set()

    cur_field = fields[fields_state]
    
    if cur_field['fieldType'] == 'COMBOBOX':
        await set_up_keyboard_paginator(lang, cur_field['fieldValues'], inline_keyboard_from_keys, state)
        await query.message.edit_text(cur_field['title'][lang], reply_markup=inline_keyboard_from_keys(lang, cur_field['fieldValues']))
        return

    await query.answer()
    await query.message.edit_text(
        cur_field["title"][lang], reply_markup=back_keyboard(lang)
    )


@dp.callback_query_handler(provider_filter, state=Payment.provider)
@has_lang
async def get_provider(lang, query: CallbackQuery, state: FSMContext, raw_state):
    provider_id = int(provider_re.findall(query.data)[0])

    async with state.proxy() as data:
        data["provider_id"] = provider_id

        category_id = data.get("category_id", 0)
        if not category_id:
            return await cancel_all(lang, query.message, state=state)

        category_data = data.get("category_data", {})
        providers = data.get("providers")

        for provider in providers:
            if provider["id"] == provider_id:
                services = provider["services"]
                data["provider_data"] = provider
                break

    services = services or []

    if not services:
        return await cancel_all(lang, query.message, state=state)

    if len(services) == 1:
        await ask_first_field(lang, services[0], query, state)
        return

    await Payment.next()
    await query.answer()
    await query.message.edit_text(
        ask_service[lang], reply_markup=services_keyboard(lang, services)
    )


@dp.callback_query_handler(service_filter, state=Payment.service)
@has_lang
async def get_service(lang, query: CallbackQuery, state: FSMContext, raw_state):

    service_id = int(service_re.findall(query.data)[0])

    async with state.proxy() as data:
        provider_data = data["provider_data"]
        services = provider_data["services"]
        service = {}
        for s in services:
            if s["id"] == service_id:
                service = s
                data["service"] = s
                break

    if not service:
        return

    await ask_first_field(lang, service, query, state)


async def ask_confirmation(message: Message, lang, card_name, card_mask, balance, state):
    global fields_info
    await Payment.confirmation.set()
    async with state.proxy() as data:
        # fields_info = data["fields_info"]
        fields_info = fields_info.get(message.chat.id)
        fields_str = "\n".join(
            [f'{field["title"]}: {field["value"]}' for field in fields_info.values()]
        )
        provider = data["provider_data"]
        service = data["service"]

        card_info = " ".join([*(card_name, card_mask)])

    await save_cur_message(
        await message.reply(
            ask_payment_confirmation[lang].format(
                provider=provider["title_short"],
                service=service["title"][lang],
                service_price=service['service_price'],
                fields_info=fields_str,
                card_info=card_info,
                balance=balance,
            ),
            reply_markup=confirmation_keyboard(lang),
        ),
        state,
    )


async def ask_cards(message: Message, lang, bearer, state):
    await Payment.card.set()
    cards = requests.get_cards(bearer)
    amount = None
    async with state.proxy() as data:
        if fields_info.get(message.chat.id) and fields_info.get(message.chat.id, {}).get('amount'):
            amount = fields_info.get(message.chat.id, {}).get('amount', {}).get('value')
        else:
            service = get_info_service(data['providers']['services'])
            service_id = service['id']
            response, balance, amount = requests.get_info(bearer, data['provider_data']['id'], service_id, fields_info.get(message.chat.id, {}))
            field = get_exact_field(data['service']['fields'], 'MONEY')
            if not fields_info.get(message.chat.id):
                fields_info.__setitem__(message.chat.id, dict())
            save_field(fields_info[message.chat.id], field['name'], field['title'][lang], amount)
        amount = int(amount)

    cards = [card for card in cards if card["is_verified"]]
    if not len(cards):
        await message.answer(verified_cards_not_found[lang])
        return

    cards = [card for card in cards if card["balance"] >= amount]

    if not len(cards):
        await message.answer(not_enough_money_in_cards[lang])
        return

    if len(cards) > 1:
        await Payment.card.set()
        await set_up_keyboard_paginator(lang, cards, cards_keyboard, state)
        await save_cur_message(
            await message.answer(
                ask_card_to_pay[lang], reply_markup=cards_keyboard(lang, cards)
            ),
            state,
        )
        return

    card = cards[0]

    card_token = card["token"]
    card_tokens.__setitem__(message.chat.id, card_token)
    card_types.__setitem__(message.chat.id, card['type'])
    async with state.proxy() as data:
        data["card_token"] = card_token
        data["card_type"] = card["type"]

    await ask_confirmation(
        message, lang, card["name"], card["mask"], card["balance"], state
    )


async def send_info(lang, bearer, message: Message, state: FSMContext):
    async with state.proxy() as data:
        msg = data.get("cur_message")
        if isinstance(msg, Message):
            msg.edit_reply_markup(None)
    
        response, balance, amount = requests.get_info(bearer, data['provider_data']['category_id'], data['service']['id'], fields_info.get(message.chat.id))
    
    if not response['status']:
        await message.answer(response['message'][lang])
        return
    
    useful_info = get_useful_info(response['data'][0]['response'])
    
    lang = 'ru' if lang == 'en' else lang
    
    key = 'label' + lang.title()
    value = 'value'
    
    string_info = '\n'.join([f'{info[key]}: {info[value]}' for info in useful_info if info[value]])
    await message.answer(string_info)
    
    await state.finish()
    
    await message.answer(main_menu_placeholder[lang], reply_markup=main_menu(lang))


@dp.callback_query_handler(state=Payment.fields)
@has_bearer
@has_lang
async def get_callback_query_field(lang, bearer, query: CallbackQuery, state: FSMContext, raw_state):
    await query.answer()
    await query.message.edit_reply_markup(None)
    async with state.proxy() as data:
        fields = data['fields']
        fields_state = data['fields_state']
        cur_field = fields[fields_state]
        value = query.data
        
        if not fields_info.get(query.from_user.id):
            fields_info.__setitem__(query.from_user.id, dict())

        text_of_btn = [elem['title'] for elem in data['keyboard_args'][1] if str(elem['key']) == value][0]
        await query.message.edit_text(
            f'{query.message.text}: {text_of_btn}'
        )
        
        save_field(fields_info.get(query.from_user.id), cur_field['name'], cur_field['title'][lang], value)
        fields_state = get_next_field_state(fields_state + 1, fields)
        
        if len(fields) <= fields_state:
            if data['service']['type_id'] == 1:
                await ask_cards(query.message, lang, bearer, state)
            else:
                await send_info(lang, bearer, query.message, state)
            return
        cur_field = fields[fields_state]
        data['fields_state'] = fields_state
        service = data['service']
    
    if cur_field['fieldType'] == 'COMBOBOX':
        await set_up_keyboard_paginator(lang, cur_field['fieldValues'], inline_keyboard_from_keys, state)
        new_text = f"{query.message.text}\n{cur_field['title'][lang]}"
        await query.message.edit_text(new_text, reply_markup=inline_keyboard_from_keys(lang, cur_field['fieldValues']))
        return
    
    text = cur_field['title'][lang]
    reply_markup = cancel_keyboard(lang)
    
    if field_type_is('PHONE', cur_field):
        reply_markup = phone_number_keyboard(lang, add_users_number=True, add_cancel=True, chat_id=query.from_user.id)
    elif field_type_is('MONEY', cur_field):
        reply_markup = amount_keyboard(lang, service)
    
    await query.message.answer(text, reply_markup=reply_markup)


@dp.message_handler(state=Payment.fields)
@has_bearer
@has_lang
async def get_field(lang, bearer_token, message: Message, state: FSMContext, raw_state):
    async with state.proxy() as data:
        fields = data["fields"]
        fields_state = data["fields_state"]

        cur_field = fields[fields_state]

        value = message.text

        if not await check_field(cur_field, value, message, lang):
            return
        
        if not fields_info.get(message.from_user.id):
            fields_info.__setitem__(message.from_user.id, dict())

        save_field(fields_info[message.chat.id], cur_field["name"], cur_field["title"][lang], value)

        fields_state = get_next_field_state(fields_state + 1, fields)

        if len(fields) <= fields_state:
            if data['service']['type_id'] == 1:
                await ask_cards(message, lang, bearer_token, state)
            else:
                await send_info(lang, bearer_token, message, state)
            return

        cur_field = fields[fields_state]

        data["fields_state"] = fields_state
        service = data['service']
    
    if cur_field['fieldType'] == 'COMBOBOX':
        await set_up_keyboard_paginator(lang, cur_field['fieldValues'], inline_keyboard_from_keys, state)
        await message.answer(cur_field['title'][lang], reply_markup=inline_keyboard_from_keys(lang, cur_field['fieldValues']))
        return
    
    text = cur_field['title'][lang]
    reply_markup = cancel_keyboard(lang)
    
    if field_type_is('PHONE', cur_field):
        reply_markup = phone_number_keyboard(lang, add_users_number=True, add_cancel=True, chat_id=message.from_user.id)
    elif field_type_is('MONEY', cur_field):
        reply_markup = amount_keyboard(lang, service)

    await message.answer(text, reply_markup=reply_markup)


@dp.message_handler(
    content_types=ContentTypes.CONTACT, state=MobilePayment.phone_number
)
@has_lang
async def get_contact(lang, message: Message, state: FSMContext, raw_state):
    phone_number = message.contact.phone_number

    async with state.proxy() as data:
        set_provider_from_phone_number(lang, phone_number[4:], data)

    await MobilePayment.next()
    await message.answer(ask_amount[lang], reply_markup=cancel_keyboard(lang))


@dp.message_handler(state=MobilePayment.phone_number)
@has_lang
async def get_phone_number(lang, message: Message, state: FSMContext, raw_state):
    pattern = re.compile(r"\+?[\d]{12}|[\d]{9}")
    if not re.match(pattern, message.text):
        await message.answer(wrong_phone_number[lang])
        return

    phone_number = message.text[1:] if "+" in message.text else message.text
    phone_number = phone_number[3:] if len(phone_number) == 12 else phone_number
    async with state.proxy() as data:
        set_provider_from_phone_number(lang, phone_number, data)

    await MobilePayment.next()
    await message.answer(ask_amount[lang], reply_markup=cancel_keyboard(lang))


@dp.message_handler(lambda message: message.text.isdigit(), state=MobilePayment.amount)
@has_bearer
@has_lang
async def get_amount(lang, bearer, message: Message, state: FSMContext, raw_state):
    if not correct_amount(message.text):
        await message.answer(wrong_amount[lang])
        return

    amount = int(message.text)

    async with state.proxy() as data:
        set_amount_for_phone_number(lang, str(amount), data)

    await ask_cards(message, lang, bearer, state)


@dp.callback_query_handler(lambda query: query.data != "back", state=Payment.card)
@has_bearer
@has_lang
async def get_card(lang, bearer, query: CallbackQuery, state: FSMContext, raw_state):
    card_token = query.data
    cards = requests.get_cards(bearer)

    card = [card for card in cards if card["token"] == card_token][0]
    card_tokens.__setitem__(query.from_user.id, card_token)
    card_tokens.__setitem__(query.from_user.id, card['type'])
    async with state.proxy() as data:
        data["card_token"] = card_token
        data["card_type"] = card["type"]

    await query.answer()

    await query.message.edit_text(
        chosen_card[lang].format(f"{card['name']} {card['mask']}"), reply_markup=None
    )

    await ask_confirmation(
        query.message, lang, card["name"], card["mask"], card["balance"], state
    )

    await Payment.confirmation.set()


@dp.callback_query_handler(state=Payment.confirmation)
@has_bearer
@has_lang
async def get_confrirmation(
    lang, bearer, query: CallbackQuery, state: FSMContext, raw_state
):
    global fields_info
    qdata = query.data
    await query.answer()

    if qdata != "confirm":
        await back_to_all_categories(lang, bearer, query, state, raw_state)
        return

    async with state.proxy() as data:
        provider = data["provider_data"]
        service = data["service"]
        fields_info = fields_info.get(query.from_user.id)
    card_token = card_tokens.get(query.from_user.id, '')
    type_id = card_types.get(query.from_user.id, '')

    data = requests.make_payment(
        bearer,
        provider["id"],
        service["id"],
        fields_info,
        card_token,
        type_id,
        query.from_user.id,
    )
    if not data['status']:
        await query.message.edit_text(data['message'][lang], reply_markup=None)
        return
    
    description = data['data'][0]['description']
    await state.finish()
    await query.message.edit_text(
        query.message.text + f'\n\n✅ {description}', reply_markup=None
    )
    await query.message.answer(main_menu_placeholder[lang], reply_markup=main_menu(lang))
