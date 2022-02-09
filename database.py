import sqlite3
from functools import lru_cache
import os

import django
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot.settings")
django.setup()

from settings.models import User


def connect(func):
    def wrapped(*args, **kwargs):
        with sqlite3.connect("database.db") as connection:
            cursor = connection.cursor()
            return func(*args, **kwargs, cur=cursor, conn=connection)

    return wrapped


def using_user(func):
    async def wrapper(chat_id, *args, **kwargs):
        user: User = await sync_to_async(User.objects.get, thread_sensitive=True)(chat_id=chat_id)
        result = await func(user, *args, **kwargs)
        await sync_to_async(user.save, thread_sensitive=True)()
        return result
    
    return wrapper


async def get_user_language(user_id):
    user: User = await sync_to_async(User.objects.get, thread_sensitive=True)(chat_id=user_id)
    return user.language


async def get_token(user_id):
    user: User = await sync_to_async(User.objects.get, thread_sensitive=True)(chat_id=user_id)
    return user.access_token


async def get_phone_number(user_id):
    user: User = await sync_to_async(User.objects.get, thread_sensitive=True)(chat_id=user_id)
    return user.phone_number


async def user_is_contact(user_id):
    user: User = await sync_to_async(User.objects.get, thread_sensitive=True)(chat_id=user_id)
    return user.phone_number_is_contact


@lru_cache
@connect
def get_user_language_old(user_id, cur, conn):
    query = "SELECT language FROM users WHERE chat_id = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    return


@connect
def user_attends(user_id, cur, conn):
    query = "SELECT chat_id FROM users WHERE chat_id = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    return bool(len(result))


async def add_user(chat_id):
    if await User.exists(chat_id):
        return
    user = User(chat_id=chat_id)
    await sync_to_async(user.save, thread_sensitive=True)()


@connect
def add_user_old(user_id, cur, conn):
    if user_attends(user_id):
        return
    query = "INSERT INTO users (chat_id) VALUES (?)"
    cur.execute(query, (user_id,))
    conn.commit()


@connect
def set_language_old(user_id, lang, cur, conn):
    query = "UPDATE users SET language = ? WHERE chat_id = ?"
    cur.execute(query, (lang, user_id))
    conn.commit()



@using_user
async def set_language(user: User, lang):
    user.language = lang


@using_user
async def set_phone_number(user: User, phone_number, user_is_contact):
    user.phone_number = phone_number
    user.phone_number_is_contact = user_is_contact


@using_user
async def set_last_otp_token(user: User, last_otp_token):
    user.last_otp_token = last_otp_token


@using_user
async def set_unired_id(user: User, unired_id):
    user.unired_id = unired_id


@using_user
async def set_user_registered(user: User):
    user.is_registered = True


@using_user
async def set_password(user: User, password):
    user.password = password


@using_user
async def save_user_info(user: User, name, last_name, access_token, expires_at):
    user.name = name
    user.last_name = last_name
    user.access_token = access_token
    user.expires_at = expires_at





@connect
def set_phone_number_old(user_id, phone_number, cur, conn):
    query = "UPDATE users SET phone_number = ? WHERE chat_id = ?"
    cur.execute(query, (phone_number, user_id))
    conn.commit()


@connect
def set_last_otp_token_old(user_id, otp_token, cur, conn):
    query = "UPDATE users SET last_otp_token = ? WHERE chat_id = ?"
    cur.execute(query, (otp_token, user_id))
    conn.commit()


@connect
def set_unired_id_old(user_id, unired_id, cur, conn):
    query = "UPDATE users SET unired_id = ? WHERE chat_id = ?"
    cur.execute(query, (unired_id, user_id))
    conn.commit()


@connect
def set_user_registered_old(user_id, cur, conn):
    query = "UPDATE users SET is_registered = ? WHERE chat_id = ?"
    cur.execute(
        query,
        (
            True,
            user_id,
        ),
    )
    conn.commit()


@connect
def set_user_unregistered(user_id, cur, conn):
    query = "UPDATE users SET is_registered = ? WHERE chat_id = ?"
    cur.execute(
        query,
        (
            False,
            user_id,
        ),
    )
    conn.commit()


@connect
def set_PIN(user_id, pin, cur, conn):
    query = "UPDATE users SET pin = ? WHERE chat_id = ?"
    cur.execute(
        query,
        (
            pin,
            user_id,
        ),
    )
    conn.commit()


@connect
def set_name(user_id, name, cur, conn):
    query = "UPDATE users SET name = ? WHERE chat_id = ?"
    cur.execute(query, (name, user_id))
    conn.commit()


@connect
def set_last_name(user_id, last_name, cur, conn):
    query = "UPDATE users SET last_name = ? WHERE chat_id = ?"
    cur.execute(query, (last_name, user_id))
    conn.commit()


@connect
def set_access_token(user_id, access_token, cur, conn):
    query = "UPDATE users SET access_token = ? WHERE chat_id = ?"
    cur.execute(query, (access_token, user_id))
    conn.commit()


@connect
def save_data(user_id, name, last_name, access_token, expires_at, cur, conn):
    set_name(user_id, name)
    set_last_name(user_id, last_name)
    set_access_token(user_id, access_token)
    query = "UPDATE users SET expires_at = ? WHERE chat_id = ?"
    cur.execute(query, (expires_at, user_id))
    conn.commit()


@lru_cache
@connect
def get_token_old(user_id, cur, conn):
    query = "SELECT access_token FROM users WHERE chat_id = ?"
    cur.execute(query, (user_id,))
    result_row = cur.fetchone()
    if result_row:
        return result_row[0]
    return ""


@lru_cache
@connect
def get_phone_number_old(chat_id, cur, conn):
    query = "SELECT phone_number FROM users WHERE chat_id = ?"
    cur.execute(query, (chat_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    return ""
