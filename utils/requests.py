import json
import logging
import time
from pprint import pprint

import requests

details = {
    "ip": "randomIP",
    "imei": "randomIMEI",
    "mac": "randomMAC",
    "name": "Python Bot",
    "lat": "Servers lat",
    "long": "Servers long",
    "firebase_reg_id": "i don't know what is it",
    "uuid": "Unique id is not found",
    "version": "1.0",
}


def get_payment_categories(token):
    url = "https://mobile.unired.uz/v4/payment/getCategoriesAll"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()
    if data["status"]:
        categories = data["data"][0]["categories"]
    else:
        logging.warn(f"{data=}\n{token=}")
        categories = []

    return categories


def get_kommunal_categories(token):
    url = "https://mobile.unired.uz/v4/payment/getCategoriesKamunal"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()
    if data["status"]:
        categories = data["data"][0]["categories"]
    else:
        logging.warn(f"{data=}\n{token=}")
        categories = []

    return categories


def get_category_providers(category_id, token):
    url = "https://mobile.unired.uz/v4/payment/getSingleCategory"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"params": {"id": category_id}}

    response = requests.post(url, json=params, headers=headers)
    data = response.json()
    if data["status"]:
        providers = data
    else:
        logging.warn(f"{data=}")
        providers = {}

    return providers


def step_one(mobile, lang):
    url = "https://mobile.unired.uz/v4/auth/step-1"
    body = {"mobile": mobile, "lang": lang}
    response = requests.post(url, json=body)
    data = response.json()
    if data["status"]:
        return data["data"][0]
    return {}


def step_two(otp_token, otp, forgot=0):
    url = "https://mobile.unired.uz/v4/auth/step-2"
    body = {"otp_token": otp_token, "otp": otp, "forgot": forgot}
    response = requests.post(url, json=body)
    data = response.json()
    if data["status"]:
        return data["data"][0]["is_registered"]
    else:
        logging.warn(f"{data=}")


def login(otp_token, password):
    url = "https://mobile.unired.uz/v4/auth/login"
    body = {"otp_token": otp_token, "password": password}
    body["details"] = details

    response = requests.post(url, json=body)
    data = response.json()
    if data["status"]:
        # logging.info(f"{data=}")
        return data["data"][0]
    else:
        logging.warn(f"{data=}")
        return {}


def register(otp_token, name, last_name, mobile, email, password):
    url = "https://mobile.unired.uz/v4/auth/register"
    body = {
        "otp_token": otp_token,
        "name": name,
        "last_name": last_name,
        "mobile": mobile,
        "email": email,
        "password": password,
        "details": details,
    }

    response = requests.post(url, json=body)
    data = response.json()
    if data["status"]:
        return data["data"][0]
    else:
        logging.warn(f"{data=}")
        return {}


def get_cards(token):
    url = "https://mobile.unired.uz/v4/card/card-details"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(url, headers=headers)
    data = response.json()

    if data["status"]:
        return data["data"]

    return {}


def make_payment(
    token, provider_id, service_id, fields_info, card_token, type_id, reg_id
):
    url = "https://mobile.unired.uz/v4/payment/perform-payment"

    headers = {"Authorization": f"Bearer {token}"}

    fields = {name: info["value"] for name, info in fields_info.items()}

    body = {
        "params": {
            "receiver": {
                "id": provider_id,
                "service_id": service_id,
                "time": int(time.time()),
                "fields": fields,
            },
            "token": card_token,
        },
        "type_id": type_id,
        "reg_id": str(reg_id),
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    pprint(data, indent=2)
    
    return data
