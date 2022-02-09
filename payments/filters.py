import re

from aiogram.dispatcher.filters import Text
from messages import start_payments_button, cancel_button

number_re = category_re = service_re = provider_re = re.compile(r"([\d]+)")


payment_start_filter = lambda message: message.text in start_payments_button.values()
cancel_filter = lambda message: message.text in cancel_button.values()
category_filter = lambda query: number_re.match(query.data)
provider_filter = lambda query: number_re.match(query.data)
service_filter = lambda query: number_re.match(query.data)
