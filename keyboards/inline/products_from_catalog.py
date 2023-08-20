from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db

product_cb = CallbackData('product', 'id', 'action')
product_send = CallbackData('product', 'id', 'action')


def product_markup(idx='', price=0, product_name='', user=''):
    global product_cb

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"Tovarni Forward qilish",
                                    callback_data=product_send.new(id=idx, action='send')))
    markup.add(InlineKeyboardButton(f"Hoziroq Sotib olish", url="https://t.me/qwertyuzb"))

    return markup
