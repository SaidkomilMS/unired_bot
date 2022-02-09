import logging
import re

from messages import ask_to_try_again


def save_field(data, name, title, value):
    if not data.get("fields_info"):
        data["fields_info"] = {}

    data["fields_info"].update({name: {"title": title, "value": value}})
    data[name] = value


async def check_field(field, value, message, lang):
    if field["fieldType"] == "REGEXBOX":
        if not re.match(field["fieldControl"], value):
            await message.reply(ask_to_try_again[lang])
            return False
    return True


def get_next_field_state(state, fields):
    while (
        len(fields) > state
        and not fields[state]["required"]
        and fields[state]["readOnly"]
    ):
        state += 1
    return state


def get_paying_service(services):
    for service in services:
        if service["type_id"] == 1:
            return service


def get_exact_field(fields, type):
    for field in fields:
        if field["fieldType"] == type:
            return field


def check_phone_code(phone_code, codes):
    return any([phone_code == code["key"] for code in codes])


def set_provider_from_phone_number(lang, phone_number, data):
    providers = data["providers"]
    for provider in providers:
        service = get_paying_service(provider["services"])
        field = get_exact_field(service["fields"], "PHONE")
        if check_phone_code(phone_number[:2], field["fieldValues"]):
            data["provider_id"] = provider["id"]
            data["provider_data"] = provider
            data["service"] = service
            save_field(data, field["name"], field["title"][lang], phone_number)
            break


def set_amount_for_phone_number(lang, amount, data):
    provider = data["provider_data"]
    service = get_paying_service(provider["services"])
    field = get_exact_field(service["fields"], "MONEY")
    save_field(data, field["name"], field["title"][lang], amount)


async def save_cur_message(message, state):
    async with state.proxy() as data:
        data["cur_message"] = message


def field_type_is(type, field):
    return field['fieldType'] == type
