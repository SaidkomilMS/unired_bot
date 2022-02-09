from aiogram.types import Message

from keyboards import languages_keyboard
from settings.states import SignIn


async def ask_lang(message: Message):
    await SignIn.first()
    await message.reply(
        """
Assalomu alaykum, {}!

O'zingizga qulay tilni tanlang:
Выберите удобный для вас язык:
Choose more convenient language for you:
        """.format(
            message.from_user.get_mention(message.from_user.full_name, as_html=True)
        ),
        reply_markup=languages_keyboard,
        parse_mode="html",
    )
