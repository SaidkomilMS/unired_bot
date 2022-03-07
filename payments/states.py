from aiogram.dispatcher.filters.state import State, StatesGroup


class Payment(StatesGroup):
    category = State()
    provider = State()
    service = State()
    fields = State()
    card = State()
    field = State()
    value = State()
    confirmation = State()


class MobilePayment(StatesGroup):
    phone_number = State()
    amount = State()
