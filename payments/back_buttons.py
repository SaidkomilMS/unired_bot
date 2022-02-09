import logging

from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.dispatcher import FSMContext

from messages import cancelled_successfull, main_menu_placeholder, ask_categroty
from utils import has_bearer, has_lang, requests
from keyboards import main_menu
from settings.main import dp

from .states import Payment
from .filters import cancel_filter
from .keyboards import (
    category_providers,
    payment_categories_keyboard,
)


@dp.message_handler(cancel_filter, state="*")
@has_lang
async def cancel_all(lang, message: Message, state: FSMContext):

    async with state.proxy() as data:
        if isinstance(data.get("cur_message"), Message):
            try:
                await data["cur_message"].delete()
                logging.info("deleted")
            except MessageToDeleteNotFound:
                logging.info("Message not found")
            data["cur_message"] == None
        else:
            logging.info("else")

    await message.answer(cancelled_successfull[lang], reply_markup=main_menu(lang))
    await state.finish()


@dp.callback_query_handler(lambda query: query.data == "back", state=Payment.category)
@has_lang
async def back_to_main_menu(lang, query: CallbackQuery, state: FSMContext, raw_state):
    async with state.proxy() as data:
        if isinstance(data.get("cur_message"), Message):
            data["cur_message"] == None

    await query.message.answer(
        main_menu_placeholder[lang], reply_markup=main_menu(lang)
    )
    await state.finish()

    await query.message.delete()


@dp.callback_query_handler(
    lambda query: query.data == "back_to_all", state=Payment.category
)
@has_bearer
@has_lang
async def back_to_all_categories(
    lang, bearer_token, query: CallbackQuery, state: FSMContext, raw_state
):
    categories = requests.get_payment_categories(bearer_token)

    await query.message.edit_text(
        ask_categroty[lang], reply_markup=payment_categories_keyboard(lang, categories)
    )


@dp.callback_query_handler(lambda query: query.data == "back", state=Payment.provider)
@has_bearer
@has_lang
async def back_to_categories(
    lang, bearer_token, query: CallbackQuery, state: FSMContext, raw_state
):
    await Payment.previous()

    categories = requests.get_payment_categories(bearer_token)

    await query.message.edit_text(
        ask_categroty[lang], reply_markup=payment_categories_keyboard(lang, categories)
    )


@dp.callback_query_handler(lambda query: query.data == "back", state=Payment.service)
@has_bearer
@has_lang
async def back_to_providers(
    lang, bearer_token, query: CallbackQuery, state: FSMContext, raw_state
):
    await Payment.previous()

    async with state.proxy() as data:
        providers = data["category_data"]["data"][0]["providers"]

    await query.message.edit_text(
        ask_categroty[lang], reply_markup=category_providers(lang, providers)
    )
