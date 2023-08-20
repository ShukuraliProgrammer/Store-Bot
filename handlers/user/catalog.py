from aiogram.types import ReplyKeyboardMarkup
import logging
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.categories import categories_markup, category_cb, subcategory_cb
from keyboards.inline.products_from_catalog import product_markup, product_cb, product_send
from aiogram.utils.callback_data import CallbackData
from aiogram.types.chat import ChatActions
from loader import dp, db, bot
from .menu import catalog
from filters import IsUser
from aiogram.dispatcher import FSMContext
from data import config


async def forward_to_user(user_id, message):
    try:
        await bot.forward_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        # Agar xatolik bo'lsa uni tekshirib ko'rsatamiz
        logging.exception(f"Xatolik yuz berdi: {e}")


@dp.callback_query_handler(IsUser(), product_send.filter(action='send'))
async def product_send_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    idx = callback_data['id']
    action = callback_data['action']
    print("text: ",query.message.text)

    user_id = 1467352173
    await bot.forward_message(chat_id=user_id, from_chat_id=query.message.chat.id,
                              message_id=query.message.message_id)


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('Mahsulotlar royxatini korsatish uchun bolimni tanlang:',
                         reply_markup=categories_markup())


@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):
    category_idx = callback_data['id']
    subcategories = db.fetchall('''SELECT * FROM subcategories subcategory
    WHERE subcategory.category = ?''', (category_idx,))
    markup = InlineKeyboardMarkup()

    for idx, title, category in subcategories:
        markup.add(InlineKeyboardButton(
            title, callback_data=subcategory_cb.new(id=idx, action='view')))

    await query.message.answer('Barcha Subkategoriyalar.', reply_markup=markup)


@dp.callback_query_handler(IsUser(), subcategory_cb.filter(action="view"))
async def subcategory_callback_handler(query: CallbackQuery, callback_data: dict):
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM subcategories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('Barcha mavjud mahsulotlar.')
    await show_products(query.message, products)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict):
    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('Mahsulot savatga qushildi!')
    await query.message.delete()


async def show_products(m, products):
    if len(products) == 0:

        await m.answer('Bu yerda hech narsa yoq ')

    else:

        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, title, body, image, price, quantity, _ in products:
            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body}\n\n{quantity}'

            await m.answer_photo(photo=image,
                                 caption=text,
                                 reply_markup=markup)


@dp.callback_query_handler(IsUser(), text="back")
async def back_menu(call: CallbackQuery):
    catalog = '🛍️ mahsulot'
    balance = '💰 Balans'
    cart = '🛒 Savatcha'
    delivery_status = '🚚 zakas holati'

    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(catalog)
    markup.add(balance, cart)
    markup.add(delivery_status)

    await call.message.delete()
    await call.message.answer("menu", reply_markup=markup)
