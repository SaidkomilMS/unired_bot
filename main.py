import logging

from aiogram.utils import executor
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext

from payments.main import dp

logging.basicConfig(level=logging.INFO)


@dp.callback_query_handler(lambda query: query.data == "prev_page", state="*")
async def prev_page(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        args = data["keyboard_args"]
        keyboard = data["keyboard"]
        page = data["page"] - 1
        data["page"] = data["page"] - 1

    await query.message.edit_reply_markup(keyboard(*args, page=page))


@dp.callback_query_handler(lambda query: query.data == "next_page", state="*")
async def prev_page(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        args = data["keyboard_args"]
        keyboard = data["keyboard"]
        page = data["page"] + 1
        data["page"] = data["page"] + 1

    await query.message.edit_reply_markup(keyboard(*args, page=page))


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
