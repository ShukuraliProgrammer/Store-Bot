from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from states import ProductState, CategoryState, SubCategoryState
from aiogram.types.chat import ChatActions
from handlers.user.menu import settings
from loader import dp, db, bot
from filters import IsAdmin
from hashlib import md5

category_cb = CallbackData('category', 'id', 'action')
subcategory_cb = CallbackData('subcategory', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

add_product = '➕ Mahsulot qoshish'
delete_category = '🗑️ katigoriyanni uchirish'
add_subcategory = '➕ Sub Kategoriya qoshish'

@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):
    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        '+ Katigoriya qoshish', callback_data='add_category'))
    await message.answer('katigoriyani sozlash:', reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    category_idx = callback_data['id']
    subcategories = db.fetchall('''SELECT * FROM subcategories subcategory
    WHERE subcategory.category = ?''', (category_idx,))
    markup = InlineKeyboardMarkup()

    for idx, title, category in subcategories:
        markup.add(InlineKeyboardButton(
            title, callback_data=subcategory_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        text='➕ Sub Kategoriya qoshish', callback_data='add_subcategory'))

    await query.message.delete()
    await query.answer('Ushbu turkumdagi barcha subcategoriyalar.')
    await state.update_data(category_index=category_idx)
    await query.message.answer("Yana qushishni hohlaysizmi ?", reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), text='add_subcategory')
async def add_subcategory_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer("Sub Kategoriya nomi ?")
    await SubCategoryState.title.set()


# subcategory
@dp.message_handler(IsAdmin(), state=SubCategoryState.title)
async def set_subcategory_category_handler(message: Message, state: FSMContext):
    title = message.text
    idx = md5(title.encode('utf-8')).hexdigest()
    async with state.proxy() as data:

        if 'category_index' in data.keys():

            category_idx = data['category_index']

            db.query('INSERT INTO subcategories VALUES (?, ?, ?)', (idx, title, category_idx))

            markup = InlineKeyboardMarkup()

            for idx, title, category in db.fetchall('SELECT * FROM subcategories subcategory WHERE subcategory.category = ?''', (category_idx,)):
                print("Sub id: ",idx)
                markup.add(InlineKeyboardButton(
                    title, callback_data=subcategory_cb.new(id=idx, action='view')))

            markup.add(InlineKeyboardButton(
                '+ Sub kategoriya qoshish', callback_data='add_subcategory'))

            await state.finish()
            await message.answer("Yana Subkategoriya qushishni hohlaysizmi ?", reply_markup=markup)


# category
@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('katigoriya nomi?')
    await CategoryState.title.set()


@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):
    category = message.text
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))

    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        '+ katigoriya qoshish', callback_data='add_category'))

    # await message.answer('Настройка категорий:', reply_markup=markup)

    await state.finish()
    await process_settings(message)


@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'category_index' in data.keys():
            idx = data['category_index']

            db.query(
                'DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)


@dp.callback_query_handler(IsAdmin(), subcategory_cb.filter(action='view'))
async def subcategory_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    subcategory_idx = callback_data['id']
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM subcategories WHERE idx=?)''',
                           (subcategory_idx,))
    await query.message.delete()
    await query.answer('Ushbu turkumdagi barcha qoshilgan mahsulotlar.')
    await state.update_data(subcategory_index=subcategory_idx)
    await show_products(query.message, products, subcategory_idx)
# add product


@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message):
    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)

    await message.answer('Ismi?', reply_markup=markup)


@dp.message_handler(IsAdmin(), text=cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Ок, bekor qilmoq!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await process_settings(message)


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)


@dp.message_handler(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text

    await ProductState.next()
    await message.answer('tavsif?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):
    await ProductState.title.set()

    async with state.proxy() as data:
        await message.answer(f"Ismni o'zgartirish с <b>{data['title']}</b>?", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['body'] = message.text

    await ProductState.next()
    await message.answer('Rasm?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO, state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):
    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    async with state.proxy() as data:
        data['image'] = downloaded_file

    await ProductState.next()
    await message.answer('narx?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.TEXT, state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):
    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:

            await message.answer(f"Tavsifni tahrirlash с <b>{data['body']}</b>?", reply_markup=back_markup())

    else:

        await message.answer('Siz mahsulotning fotosuratini yuborishingiz kerak.')


@dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(), state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):
    if message.text == back_message:

        await ProductState.image.set()

        async with state.proxy() as data:

            await message.answer("Boshqa rasm?", reply_markup=back_markup())

    else:

        await message.answer('Narxni raqam sifatida belgilang!')


@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.price)
async def process_price(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text


        await ProductState.next()

        await message.answer("Soni ?", reply_markup=back_markup())

@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.quantity)
async def process_body(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['quantity'] = message.text

        title = data['title']
        body = data['body']
        price = data['price']
        quantity = message.text
        await ProductState.next()
        text = f'<b>{title}</b>\n\n{body}\n\nNarx: {price} Sum.\n\nSoni: {quantity}'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)


@dp.message_handler(IsAdmin(), lambda message: message.text not in [back_message, all_right_message],
                    state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer('Bunday imkoniyat yoq edi..')


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):
    await ProductState.price.set()

    async with state.proxy() as data:
        await message.answer(f"Narxni taxrirlash с <b>{data['price']}</b>?", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=all_right_message, state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:

        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']
        quantity = data['quantity']

        tag = db.fetchone(
            'SELECT title FROM subcategories WHERE idx=?', (data['subcategory_index'],))[0]
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()
        db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), quantity, tag))

    await message.answer('tastiqlash!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await process_settings(message)


# delete product


@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict):
    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('ochirish!')
    await query.message.delete()


async def show_products(m, products, category_idx):
    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    for idx, title, body, image, price, quantity, tag in products:
        text = f'<b>{title}</b>\n\n{body}\n\nnarx: {price} Sum.\n\nSoni: {quantity}'

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            '🗑️ ochirish', callback_data=product_cb.new(id=idx, action='delete')))

        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(add_product)
    markup.add(delete_category)

    await m.answer('Biror narsani qoshish yoki olib tashlashni xohlaysizmi?', reply_markup=markup)
