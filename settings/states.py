from aiogram.dispatcher.filters.state import State, StatesGroup


class Register(StatesGroup):
    name = State()
    last_name = State()
    email = State()
    password = State()


class SignIn(StatesGroup):
    language = State()
    phone_number = State()
    SMScode = State()
    password = State()
