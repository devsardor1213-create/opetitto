import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo, MenuButtonWebApp, MenuButtonDefault
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import BOT_TOKEN, ADMINS, ADMIN_PASSWORD, WEBAPP_URL
from database import Database


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
db = Database()

async def is_admin(user_id):
    db_admins = await db.get_admins()
    return user_id in ADMINS or user_id in db_admins

# --- Keyboards ---
def get_start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Kafe + Bino"), KeyboardButton(text="🛵 Masofaviy")],
            [KeyboardButton(text="📦 Kuryer bo'lish"), KeyboardButton(text="👤 Kabinetim")],
            [KeyboardButton(text="☎️ Admin bilan aloqa")]
        ],
        resize_keyboard=True
    )

def get_kafe_bino_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚪 Xona"), KeyboardButton(text="🍽 Kafe")],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ], resize_keyboard=True
    )

def get_webapp_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Menyu", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ], resize_keyboard=True
    )

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ MENU qo'shish"), KeyboardButton(text="📝 O'chirish / Tahrirlash")],
            [KeyboardButton(text="📢 Reklama tarqatish"), KeyboardButton(text="👥 Foydalanuvchilar")],
            [KeyboardButton(text="🚚 Kuryerlar ma'lumotlari"), KeyboardButton(text="⚙️ Aloqa sozlamalari")],
            [KeyboardButton(text="👨‍💻 Adminlar"), KeyboardButton(text="🏷 Kategoriyalar")],
            [KeyboardButton(text="🔄 Balansni nolga tushirish")],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )

def get_contact_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)], [KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True)

def get_location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)], 
            [KeyboardButton(text="⏩ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ], 
        resize_keyboard=True
    )

# --- States ---
class AdminLogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

class AdminContact(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_username = State()

class AdminManage(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_name = State()
    
class CategoryManage(StatesGroup):
    waiting_for_new_category = State()

class AddProduct(StatesGroup):
    waiting_for_name = State()
    waiting_for_category = State()
    waiting_for_desc = State()
    waiting_for_price = State()
    waiting_for_image = State()

class Broadcast(StatesGroup):
    waiting_for_message = State()

class OrderFlow(StatesGroup):
    waiting_for_room = State()
    waiting_for_table = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_comment = State()
    
    waiting_for_type_after_checkout = State()
    waiting_for_room_after_checkout = State()
    waiting_for_table_after_checkout = State()

class CourierReg(StatesGroup):
    waiting_for_password = State()
    waiting_for_name = State()
    waiting_for_phone = State()

class AssignCourier(StatesGroup):
    waiting_for_courier_id = State()

# --- USER HANDLERS ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.add_user(message.from_user.id, message.from_user.full_name)
    
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id, 
            menu_button=MenuButtonDefault()
        )
    except Exception as e:
        print(f"Menu button set error: {e}")

    await message.answer(
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        "🔥 <b>Food Markaziga xush kelibsiz!</b>\n\n"
        "📖 <b>Qisqacha qo'llanma:</b>\n"
        "1️⃣ Avval yetkazib berish turini tanlang:\n"
        "   🏢 <b>Kafe + Bino:</b> Kafeda o'tirganingizda yoki bino xonalariga yetkazish uchun.\n"
        "   🛵 <b>Masofaviy:</b> Uyingizga yoki boshqa manzilga eltib berish uchun.\n"
        "2️⃣ So'ngra <b>🍔 Menyu</b> tugmasi paydo bo'ladi, o'sha yerdan mahsulot tanlab xaridni yakunlaysiz.\n\n"
        "👇 Iltimos, o'zingizga kerakli bo'limni tanlang:",
        reply_markup=get_start_keyboard()
    )

@dp.message(F.text == "🔙 Asosiy menyu")
@dp.message(F.text == "❌ Bekor qilish")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyuga qaytdingiz.", reply_markup=get_start_keyboard())

# --- ORDER FLOW START ---
@dp.message(F.text == "🏢 Kafe + Bino")
async def kafe_bino(message: Message, state: FSMContext):
    await message.answer("Joylashuvni tanlang:", reply_markup=get_kafe_bino_keyboard())

@dp.message(F.text == "🚪 Xona")
async def choose_xona(message: Message, state: FSMContext):
    await state.update_data(order_type="Xona")
    await message.answer("Xona raqamini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(OrderFlow.waiting_for_room)

@dp.message(OrderFlow.waiting_for_room, F.text)
async def process_room(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    await message.answer(f"Xona: {message.text}. Tasdiqlandi!\n\nPastdagi <b>🍔 Menyu</b> tugmasini bosib mahsulot tanlang:", reply_markup=get_webapp_keyboard())

@dp.message(F.text == "🍽 Kafe")
async def choose_kafe(message: Message, state: FSMContext):
    await state.update_data(order_type="Kafe")
    await message.answer("Stol raqamini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(OrderFlow.waiting_for_table)

@dp.message(OrderFlow.waiting_for_table, F.text)
async def process_table(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    await message.answer(f"Stol: {message.text}. Tasdiqlandi!\n\nPastdagi <b>🍔 Menyu</b> tugmasini bosib mahsulot tanlang:", reply_markup=get_webapp_keyboard())

@dp.message(F.text == "🛵 Masofaviy")
async def choose_masofaviy(message: Message, state: FSMContext):
    await state.update_data(order_type="Masofaviy", room_table="Yo'q")
    await message.answer("Masofaviy buyurtma!\nPastdagi <b>🍔 Menyu</b> tugmasini bosib mahsulot tanlang:", reply_markup=get_webapp_keyboard())

# --- COURIER REGISTRATION ---
@dp.message(F.text == "📦 Kuryer bo'lish")
async def kuryer_reg_start(message: Message, state: FSMContext):
    await message.answer("Kuryer bo'lish uchun maxfiy parolni kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(CourierReg.waiting_for_password)

@dp.message(CourierReg.waiting_for_password)
async def kuryer_reg_password(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    if message.text == "1155":
        await message.answer("✅ Parol to'g'ri!\n\nIltimos, ism va familiyangizni kiriting:")
        await state.set_state(CourierReg.waiting_for_name)
    else:
        await message.answer("❌ Noto'g'ri parol! Kuryer bo'lish uchun parolni bilishingiz kerak.")

@dp.message(CourierReg.waiting_for_name)
async def kuryer_reg_name(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(name=message.text)
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=get_contact_keyboard())
    await state.set_state(CourierReg.waiting_for_phone)

@dp.message(CourierReg.waiting_for_phone, F.contact | F.text)
async def kuryer_reg_phone(message: Message, state: FSMContext):
    if message.text and message.text == "❌ Bekor qilish": return await back_to_main(message, state)
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    name = data['name']
    
    courier = await db.add_courier(message.from_user.id, name, phone)
    await state.clear()
    
    await message.answer(f"✅ Siz kuryer sifatida ro'yxatdan o'tdingiz!\nSizning ID raqamingiz: <b>{courier['id']}</b>\nBuyurtmalar tushishini kuting.", reply_markup=get_start_keyboard())
    
    all_admins = set(ADMINS + await db.get_admins())
    for a_id in all_admins:
        try:
            await bot.send_message(a_id, f"🆕 <b>YANGI KURYER</b>\nID: {courier['id']}\nIsm: {name}\nTel: {phone}")
        except: pass

# --- CABINET & ORDERS ---
@dp.message(F.text == "👤 Kabinetim")
async def cmd_cabinet(message: Message):
    stats = await db.get_user_stats(message.from_user.id)
    text = (
        "👤 <b>Foydalanuvchi kabineti</b>\n\n"
        f"👤 <b>Ism:</b> {message.from_user.full_name}\n"
        f"🆔 <b>ID:</b> {message.from_user.id}\n\n"
        f"📦 <b>Jami xaridlar soni:</b> {stats['order_count']} ta\n"
        f"💸 <b>Sarflangan summa:</b> {stats['total_spent']:,} so'm".replace(',', ' ')
    )
    await message.answer(text)

@dp.message(F.text == "📦 Buyurtmalarim")
async def cmd_my_orders(message: Message):
    orders = await db.get_user_orders(message.from_user.id, limit=5)
    if not orders:
        return await message.answer("Sizda hali buyurtmalar yo'q.")
        
    text = "📦 <b>Sizning oxirgi 5 ta buyurtmangiz:</b>\n\n"
    for o in orders:
        text += f"🔖 <b>Buyurtma #{o['id']}</b> ({o.get('order_type', 'Oddiy')})\n"
        text += f"📅 Sana: {o['created_at']}\n"
        text += "🛍 <b>Mahsulotlar:</b>\n"
        for item in o.get('items', []):
            text += f"  ▪️ {item['name']} x {item['quantity']}\n"
        text += f"💰 Jami: {o['total_price']:,} so'm\n".replace(',', ' ')
        text += f"📊 Holati: <b>{o['status']}</b>\n\n"
        
    await message.answer(text)

@dp.message(F.text == "☎️ Admin bilan aloqa")
async def cmd_contact_admin(message: Message):
    contact = await db.get_admin_contact()
    name = contact.get('name', 'Fast Food Admin')
    phone = contact.get('phone', '+998 90 123 45 67')
    username = contact.get('username', '@admin')
    
    await message.answer(
        "📞 <b>Admin bilan bog'lanish:</b>\n\n"
        f"👨‍💼 Ism: {name}\n"
        f"📱 Telefon: {phone}\n"
        f"💬 Telegram: {username}\n\n"
    )

# --- CHECKOUT FLOW ---
@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    order_type = data.get("order_type")
    
    try:
        web_data = json.loads(message.web_app_data.data)
        if web_data.get('action') == 'checkout':
            items = web_data['items']
            
            db_products = await db.get_products()
            product_dict = {p['id']: p['price'] for p in db_products}
            
            total = 0
            for item in items:
                real_price = product_dict.get(int(item['id']), item.get('price', 0))
                item['price'] = real_price
                total += real_price * int(item['quantity'])
                
            await state.update_data(items=items, total=total)
            
            if not order_type:
                text = "🛍 <b>Savat qabul qilindi!</b>\n\nIltimos, buyurtmani rasmiylashtirish uchun yetkazib berish turini tanlang:"
                await message.answer(text, reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🏢 Kafe + Bino"), KeyboardButton(text="🛵 Masofaviy")]],
                    resize_keyboard=True
                ))
                await state.set_state(OrderFlow.waiting_for_type_after_checkout)
                return
            
            text = "🛍 <b>Savat qabul qilindi.</b>\nSiz quyidagi mahsulotlarni tanladingiz:\n\n"
            for item in items:
                text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(',', ' ')
            text += f"\n💰 <b>Jami summa:</b> {total:,} so'm\n\n".replace(',', ' ')
            text += "Iltimos, tasdiqlash uchun <b>📱 Raqamni yuborish</b> tugmasi orqali telefoningizni yuboring:"
            
            await message.answer(text, reply_markup=get_contact_keyboard())
            await state.set_state(OrderFlow.waiting_for_phone)
    except Exception as e:
         print(e)
         await message.answer("Buyurtmani qayta ishlashda xatolik yuz berdi.")

@dp.message(OrderFlow.waiting_for_type_after_checkout, F.text)
async def process_type_after_checkout(message: Message, state: FSMContext):
    if message.text == "🏢 Kafe + Bino":
        await message.answer("Joylashuvni tanlang:", reply_markup=get_kafe_bino_keyboard())
    elif message.text == "🚪 Xona":
        await state.update_data(order_type="Xona")
        await message.answer("Xona raqamini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
        await state.set_state(OrderFlow.waiting_for_room_after_checkout)
    elif message.text == "🍽 Kafe":
        await state.update_data(order_type="Kafe")
        await message.answer("Stol raqamini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
        await state.set_state(OrderFlow.waiting_for_table_after_checkout)
    elif message.text == "🛵 Masofaviy":
        await state.update_data(order_type="Masofaviy", room_table="Yo'q")
        
        data = await state.get_data()
        items = data['items']
        total = data['total']
        text = "🛍 <b>Yetkazib berish turi: Masofaviy</b>\nSiz quyidagi mahsulotlarni tanladingiz:\n\n"
        for item in items:
            text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(',', ' ')
        text += f"\n💰 <b>Jami summa:</b> {total:,} so'm\n\n".replace(',', ' ')
        text += "Iltimos, tasdiqlash uchun <b>📱 Raqamni yuborish</b> tugmasi orqali telefoningizni yuboring:"
        
        await message.answer(text, reply_markup=get_contact_keyboard())
        await state.set_state(OrderFlow.waiting_for_phone)

@dp.message(OrderFlow.waiting_for_room_after_checkout, F.text)
async def process_room_after_checkout(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    
    data = await state.get_data()
    items = data['items']
    total = data['total']
    text = f"🏢 <b>Xona: {message.text}</b> Tasdiqlandi!\n\n"
    text += "🛍 <b>Sizning tanlovingiz:</b>\n"
    for item in items:
        text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(',', ' ')
    text += f"\n💰 <b>Jami summa:</b> {total:,} so'm\n\n".replace(',', ' ')
    text += "Iltimos, tasdiqlash uchun <b>📱 Raqamni yuborish</b> tugmasi orqali telefoningizni yuboring:"
    
    await message.answer(text, reply_markup=get_contact_keyboard())
    await state.set_state(OrderFlow.waiting_for_phone)

@dp.message(OrderFlow.waiting_for_table_after_checkout, F.text)
async def process_table_after_checkout(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    
    data = await state.get_data()
    items = data['items']
    total = data['total']
    text = f"🍽 <b>Stol: {message.text}</b> Tasdiqlandi!\n\n"
    text += "🛍 <b>Sizning tanlovingiz:</b>\n"
    for item in items:
        text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(',', ' ')
    text += f"\n💰 <b>Jami summa:</b> {total:,} so'm\n\n".replace(',', ' ')
    text += "Iltimos, tasdiqlash uchun <b>📱 Raqamni yuborish</b> tugmasi orqali telefoningizni yuboring:"
    
    await message.answer(text, reply_markup=get_contact_keyboard())
    await state.set_state(OrderFlow.waiting_for_phone)

@dp.message(OrderFlow.waiting_for_phone, F.contact | F.text)
async def process_phone(message: Message, state: FSMContext):
    if message.text and message.text == "❌ Bekor qilish": return await back_to_main(message, state)
        
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    
    data = await state.get_data()
    if data.get("order_type") == "Masofaviy":
        await message.answer("Endi yetkazib berish uchun manzilingizni yozing (yoki lokatsiya yuboring):", reply_markup=get_location_keyboard())
        await state.set_state(OrderFlow.waiting_for_address)
    else:
        await message.answer("Qo'shimcha izoh qoldiring (Masalan: Tezroq, Pishloq ko'proq):\nYoki shunchaki 'Yoq' deb yozing.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Yo'q")]], resize_keyboard=True))
        await state.set_state(OrderFlow.waiting_for_comment)

@dp.message(OrderFlow.waiting_for_address, F.location | F.text)
async def process_address(message: Message, state: FSMContext):
    if message.text and message.text == "❌ Bekor qilish": return await back_to_main(message, state)
        
    location = "Kiritilmagan"
    if message.location:
        location = f"{message.location.latitude},{message.location.longitude}"
    elif message.text and message.text != "⏩ O'tkazib yuborish":
        location = message.text
    await state.update_data(location=location)
    
    await message.answer("Qo'shimcha izoh qoldiring (Yoki 'Yoq' deb yozing):", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Yo'q")]], resize_keyboard=True))
    await state.set_state(OrderFlow.waiting_for_comment)

def format_location(loc):
    if loc != "Yo'q" and loc != "Kiritilmagan" and "," in loc and not any(c.isalpha() for c in loc):
        return f"https://maps.google.com/?q={loc}"
    return loc

@dp.message(OrderFlow.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    comment = message.text
    data = await state.get_data()
    
    order_type = data.get("order_type", "Oddiy")
    room_table = data.get("room_table", "Yo'q")
    phone = data.get("phone")
    location = data.get("location", "Yo'q")
    items = data['items']
    total = data['total']
    
    order_id = await db.create_order(message.from_user.id, total, location, phone, items, order_type, room_table, comment)
    
    # Adminga yuborish
    from datetime import datetime
    admin_text = f"🆕 <b>YANGI BUYURTMA #{order_id}</b>\n\n"
    admin_text += f"📊 <b>Turi:</b> {order_type}\n"
    
    if order_type == "Xona": admin_text += f"🚪 <b>Xona:</b> {room_table}\n"
    elif order_type == "Kafe": admin_text += f"🍽 <b>Stol:</b> {room_table}\n"
    elif order_type == "Masofaviy": admin_text += f"📍 <b>Manzil:</b> {format_location(location)}\n"
    
    admin_text += f"👤 Ism: {message.from_user.full_name}\n"
    admin_text += f"📱 Tel: {phone}\n"
    admin_text += f"💬 Izoh: {comment}\n\n"
    admin_text += "🛍 <b>Mahsulotlar:</b>\n"
    for item in items:
        admin_text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']} so'm\n"
    admin_text += f"\n💰 <b>Jami: {total:,} so'm</b>".replace(',', ' ')
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"acc_{order_id}"), InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"rej_{order_id}")]
    ])
    
    all_admins = set(ADMINS + await db.get_admins())
    for admin_id in all_admins:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=markup)
        except: pass
            
    await state.clear()
    
    success_text = f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
    success_text += f"🔖 <b>Buyurtma raqami:</b> #{order_id}\n"
    success_text += "🛍 <b>Xaridingiz:</b>\n"
    for item in items:
        success_text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(',', ' ')
    success_text += f"\n💰 <b>Jami summa:</b> {total:,} so'm\n\n".replace(',', ' ')
    success_text += "Adminlar tez orada ko'rib chiqishadi."
    
    await message.answer(success_text, reply_markup=get_start_keyboard())

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if await is_admin(message.from_user.id):
        await message.answer("Admin paneliga xush kelibsiz!", reply_markup=get_admin_keyboard())
    else:
        await message.answer("Siz admin emassiz.\n\nLoginni kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
        await state.set_state(AdminLogin.waiting_for_login)

@dp.message(AdminLogin.waiting_for_login)
async def admin_login_step(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(admin_login=message.text)
    await message.answer("Parolni kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AdminLogin.waiting_for_password)

@dp.message(AdminLogin.waiting_for_password)
async def admin_password_step(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    login = (await state.get_data()).get('admin_login')
    password = message.text
    
    accounts = await db.get_admin_accounts()
    valid = False
    name = ""
    for acc in accounts:
        if acc['login'] == login and acc['password'] == password:
            valid = True
            name = acc['name']
            break
            
    if valid or (login == "superadmin" and password == ADMIN_PASSWORD):
        await db.set_admin_session(message.from_user.id, name if valid else "Asosiy Admin")
        await message.answer(f"✅ Muvaffaqiyatli kirdingiz, {name if valid else 'Asosiy Admin'}!", reply_markup=get_admin_keyboard())
        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri login yoki parol.")
        await state.clear()

# --- ADMIN ACTIONS ON ORDERS ---
@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    order_id = int(call.data.split("_")[1])
    await db.update_order_status(order_id, "Qabul qilindi va tayyorlanmoqda")
    
    orders = db.orders
    order = next((o for o in orders if o['id'] == order_id), None)
    
    inline_keyboard = []
    if order and order.get('order_type') == "Masofaviy":
        inline_keyboard.append([InlineKeyboardButton(text="🚚 Kuryerga berish", callback_data=f"sendcour_{order_id}")])
        
        admin_name = await db.get_admin_session(call.from_user.id)
        await call.message.edit_text(call.message.text + f"\n\n✅ Qabul qildi: <b>{admin_name}</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard))
    else:
        await call.message.edit_text(call.message.text + "\n\n✅ <b>Qabul qilindi</b>")
    await call.answer("Buyurtma qabul qilindi.")
    
    if order:
        try:
             await bot.send_message(chat_id=order['user_id'], text=f"🎉 Buyurtma #{order_id} qabul qilindi va tayyorlanmoqda!")
        except: pass

@dp.callback_query(F.data.startswith("rej_"))
async def reject_order(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    order_id = int(call.data.split("_")[1])
    
    admin_name = await db.get_admin_session(call.from_user.id)
    await db.update_order_status(order_id, "Bekor qilingan")
    await call.answer("Buyurtma bekor qilindi.")
    await call.message.edit_text(call.message.text + f"\n\n❌ Bekor qildi: <b>{admin_name}</b>")
    
    orders = db.orders
    order = next((o for o in orders if o['id'] == order_id), None)
    if order:
        try:
             await bot.send_message(chat_id=order['user_id'], text=f"❌ Uzr, sizning #{order_id} buyurtmangiz bekor qilindi.")
        except: pass

@dp.callback_query(F.data.startswith("sendcour_"))
async def prompt_courier_id(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[1])
    await state.update_data(assign_order_id=order_id)
    await state.set_state(AssignCourier.waiting_for_courier_id)
    await call.message.answer(f"Buyurtma #{order_id} qaysi kuryerga biriktiriladi?\nIltimos, Kuryer ID raqamini yozing:")
    await call.answer()

@dp.message(AssignCourier.waiting_for_courier_id)
async def assign_courier(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Faqat raqam kiriting!")
    courier_id = int(message.text)
    
    couriers = await db.get_couriers()
    courier = next((c for c in couriers if c['id'] == courier_id), None)
    
    if not courier:
         return await message.answer("Bunday ID li kuryer topilmadi!")
         
    data = await state.get_data()
    order_id = data['assign_order_id']
    
    orders = db.orders
    order = next((o for o in orders if o['id'] == order_id), None)
    if order:
         db.save_data()  # Removed await here
         c_text = f"📦 <b>YANGI MASOFAVIY BUYURTMA</b>\n\n"
         c_text += f"📍 Manzil: {format_location(order['location'])}\n"
         c_text += f"📱 Mijoz tel: {order['phone']}\n"
         c_text += f"💬 Izoh: {order['comment']}\n\n"
         c_text += "🛍 <b>Mahsulotlar:</b>\n"
         for item in order['items']:
             c_text += f"▪️ {item['name']} x {item['quantity']}\n"
         c_text += f"\n💰 Olinadigan summa: {order['total_price']:,} so'm".replace(',', ' ')
         
         try:
             await bot.send_message(courier['telegram_id'], c_text)
             await message.answer(f"✅ Buyurtma Kuryer #{courier_id} ({courier['fullname']}) ga yuborildi!")
             
             # Notify customer
             cust_text = f"🛵 <b>Sizning kuryeringiz:</b>\n\n"
             cust_text += f"👤 Ism: {courier['fullname']}\n"
             cust_text += f"📱 Tel: {courier['phone']}\n\nTez orada yetib boradi!"
             await bot.send_message(order['user_id'], cust_text)
         except Exception as e:
             await message.answer(f"Kuryer yoki Mijozga xabar yuborishda xatolik: {e}")
             
    await state.clear()

@dp.message(F.text == "🚚 Kuryerlar ma'lumotlari")
async def admin_couriers(message: Message):
    if not await is_admin(message.from_user.id): return
    couriers = await db.get_couriers()
    if not couriers: return await message.answer("Hozircha kuryerlar yo'q.")
    
    keyboard = []
    text = f"🚚 <b>Barcha kuryerlar ({len(couriers)} ta):</b>\n\n"
    for c in couriers:
        text += f"🆔 <b>{c['id']}</b> | {c['fullname']} | {c['phone']}\n"
        keyboard.append([InlineKeyboardButton(text=f"❌ {c['fullname']} ({c['id']}) ni o'chirish", callback_data=f"delcour_{c['id']}")])
        
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("delcour_"))
async def admin_delete_courier(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    courier_id = int(call.data.split("_")[1])
    await db.delete_courier(courier_id)
    
    await call.answer("Kuryer o'chirildi!")
    
    couriers = await db.get_couriers()
    if not couriers:
        await call.message.edit_text("Hozircha kuryerlar yo'q.")
        return
        
    keyboard = []
    text = f"🚚 <b>Barcha kuryerlar ({len(couriers)} ta):</b>\n\n"
    for c in couriers:
        text += f"🆔 <b>{c['id']}</b> | {c['fullname']} | {c['phone']}\n"
        keyboard.append([InlineKeyboardButton(text=f"❌ {c['fullname']} ({c['id']}) ni o'chirish", callback_data=f"delcour_{c['id']}")])
        
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.message(F.text == "👥 Foydalanuvchilar")
async def admin_users(message: Message):
    if not await is_admin(message.from_user.id): return
    users = await db.get_all_users()
    text = f"👥 <b>Barcha foydalanuvchilar ({len(users)} ta):</b>\n\n"
    for u in users[:20]:
        text += f"ID: {u.get('telegram_id')} | Ism: {u.get('fullname')}\n"
    await message.answer(text)

@dp.message(F.text == "🔄 Balansni nolga tushirish")
async def admin_reset_revenue(message: Message):
    if not await is_admin(message.from_user.id): return
    await db.reset_revenue()
    await message.answer("✅ Barcha daromadlar nolga tushirildi (Archivlandi).", reply_markup=get_admin_keyboard())

@dp.message(F.text == "⚙️ Aloqa sozlamalari")
async def admin_update_contact_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    contact = await db.get_admin_contact()
    name = contact.get('name', 'Fast Food Admin')
    await message.answer(f"Hozirgi ism: {name}\n\nYangi ismni kiriting (masalan: Murodjon):", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AdminContact.waiting_for_name)

@dp.message(AdminContact.waiting_for_name)
async def admin_update_contact_name(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(contact_name=message.text)
    contact = await db.get_admin_contact()
    await message.answer(f"Hozirgi telefon raqam: {contact['phone']}\n\nYangi telefon raqamni kiriting (masalan: +998901234567):")
    await state.set_state(AdminContact.waiting_for_phone)

@dp.message(AdminContact.waiting_for_phone)
async def admin_update_contact_phone(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(contact_phone=message.text)
    contact = await db.get_admin_contact()
    await message.answer(f"Hozirgi Telegram username: {contact['username']}\n\nYangi usernameni kiriting (masalan: @yangi_admin):")
    await state.set_state(AdminContact.waiting_for_username)

@dp.message(AdminContact.waiting_for_username)
async def admin_update_contact_username(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    data = await state.get_data()
    name = data['contact_name']
    phone = data['contact_phone']
    username = message.text
    await db.update_admin_contact(name, phone, username)
    await state.clear()
    await message.answer("✅ Aloqa ma'lumotlari muvaffaqiyatli yangilandi!", reply_markup=get_admin_keyboard())

@dp.message(F.text == "👨‍💻 Adminlar")
async def admin_manage_accounts(message: Message):
    if not await is_admin(message.from_user.id): return
    accounts = await db.get_admin_accounts()
    text = "👨‍💻 <b>Mavjud Adminlar ro'yxati:</b>\n\n"
    keyboard = []
    for acc in accounts:
        text += f"👤 {acc['name']} (Login: {acc['login']})\n"
        if acc['login'] != "admin": # Default superadmin override safety
            keyboard.append([InlineKeyboardButton(text=f"❌ {acc['name']} ni o'chirish", callback_data=f"deladmin_{acc['login']}")])
            
    keyboard.insert(0, [InlineKeyboardButton(text="➕ Yangi Admin qo'shish", callback_data="add_admin_acc")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data == "add_admin_acc")
async def add_admin_acc_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await call.message.answer("Yangi admin uchun LOGIN kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AdminManage.waiting_for_login)

@dp.message(AdminManage.waiting_for_login)
async def add_admin_login(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(new_login=message.text)
    await message.answer("Yangi admin uchun PAROL kiriting:")
    await state.set_state(AdminManage.waiting_for_password)

@dp.message(AdminManage.waiting_for_password)
async def add_admin_password(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(new_pass=message.text)
    await message.answer("Adminning ismini kiriting (masalan: Bektosh):")
    await state.set_state(AdminManage.waiting_for_name)

@dp.message(AdminManage.waiting_for_name)
async def add_admin_name(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    data = await state.get_data()
    await db.add_admin_account(data['new_login'], data['new_pass'], message.text)
    await state.clear()
    await message.answer(f"✅ Yangi admin qo'shildi!\nLogin: {data['new_login']}\nParol: {data['new_pass']}", reply_markup=get_admin_keyboard())

@dp.callback_query(F.data.startswith("deladmin_"))
async def delete_admin_acc(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    login = call.data.split("_", 1)[1]
    await db.remove_admin_account(login)
    await call.answer("Admin o'chirildi.")
    await admin_manage_accounts(call.message)

@dp.message(F.text == "🏷 Kategoriyalar")
async def admin_manage_categories(message: Message):
    if not await is_admin(message.from_user.id): return
    cats = await db.get_categories()
    text = "🏷 <b>Mavjud Kategoriyalar:</b>\n\n"
    keyboard = []
    for c in cats:
        text += f"▪️ {c}\n"
        keyboard.append([InlineKeyboardButton(text=f"❌ {c} ni o'chirish", callback_data=f"delcat_{c}")])
    keyboard.insert(0, [InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="add_cat_start")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data == "add_cat_start")
async def add_cat_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await call.message.answer("Yangi kategoriya nomini kiriting (masalan: 🍰 Pishiriqlar):", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(CategoryManage.waiting_for_new_category)

@dp.message(CategoryManage.waiting_for_new_category)
async def add_cat_finish(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await db.add_category(message.text)
    await state.clear()
    await message.answer(f"✅ Kategoriya qo'shildi: {message.text}", reply_markup=get_admin_keyboard())

@dp.callback_query(F.data.startswith("delcat_"))
async def delete_cat(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    cat = call.data.split("_", 1)[1]
    await db.remove_category(cat)
    await call.answer("Kategoriya o'chirildi.")
    await admin_manage_categories(call.message)

@dp.message(F.text == "➕ MENU qo'shish")
async def admin_add_product_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("🍔 Yangi mahsulot nomini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AddProduct.waiting_for_name)

@dp.message(AddProduct.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    categories = await db.get_categories()
    kb_buttons = []
    row = []
    for cat in categories:
        row.append(KeyboardButton(text=cat))
        if len(row) == 2:
            kb_buttons.append(row)
            row = []
    if row:
        kb_buttons.append(row)
        
    keyboard = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)
    
    await message.answer("Kategoriyani tanlang:", reply_markup=keyboard)
    await state.set_state(AddProduct.waiting_for_category)

@dp.message(AddProduct.waiting_for_category)
async def add_product_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("📝 Mahsulot tavsifini yozing:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AddProduct.waiting_for_desc)

@dp.message(AddProduct.waiting_for_desc)
async def add_product_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("💰 Narxini kiriting (raqamda):")
    await state.set_state(AddProduct.waiting_for_price)

@dp.message(AddProduct.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Faqat raqam kiriting!")
    await state.update_data(price=int(message.text))
    await message.answer("🖼 Endi mahsulot rasmini yuboring (Rasm fayli ko'rinishida yoki rasm linkini matn qilib):")
    await state.set_state(AddProduct.waiting_for_image)

@dp.message(AddProduct.waiting_for_image)
async def add_product_image(message: Message, state: FSMContext):
    data = await state.get_data()
    
    image_url = ""
    if message.photo:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        import os
        os.makedirs("webapp/images", exist_ok=True)
        file_path = f"webapp/images/{file_id}.jpg"
        await bot.download_file(file.file_path, file_path)
        image_url = f"images/{file_id}.jpg"
    elif message.text and message.text.startswith("http"):
        image_url = message.text
    else:
        await message.answer("Noto'g'ri rasm! Rasmni rasm qilib yuboring yoki URL link bering:")
        return
        
    await db.add_product(data['name'], data['desc'], data['price'], category=data['category'], image=image_url)
    await state.clear()
    await message.answer("✅ Mahsulot qo'shildi!", reply_markup=get_admin_keyboard())

@dp.message(F.text == "📝 O'chirish / Tahrirlash")
async def admin_edit_products(message: Message):
    if not await is_admin(message.from_user.id): return
    all_products = db.products
    if not all_products: return await message.answer("Mahsulotlar yo'q.")
    
    keyboard = []
    for p in all_products:
        status = "✅" if p.get('is_active', 1) else "❌"
        keyboard.append([InlineKeyboardButton(text=f"{status} {p['name']} (O'chirish/Yoqish)", callback_data=f"del_{p['id']}")])
        
    await message.answer("O'chirish yoki Yoqish uchun ustiga bosing:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("del_"))
async def admin_delete_product(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    product_id = int(call.data.split("_")[1])
    await db.toggle_product(product_id)
    
    all_products = db.products
    keyboard = []
    for p in all_products:
        status = "✅" if p.get('is_active', 1) else "❌"
        keyboard.append([InlineKeyboardButton(text=f"{status} {p['name']} (O'chirish/Yoqish)", callback_data=f"del_{p['id']}")])
    
    await call.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await call.answer("Holati o'zgartirildi!")

@dp.message(F.text == "📢 Reklama tarqatish")
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("Reklama matnini yoki rasm/videoni yuboring:")
    await state.set_state(Broadcast.waiting_for_message)

@dp.message(Broadcast.waiting_for_message)
async def admin_broadcast_send(message: Message, state: FSMContext):
    users = await db.get_all_users()
    count = 0
    for u in users:
        try:
            await bot.copy_message(chat_id=u.get('telegram_id'), from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except: pass
    await state.clear()
    await message.answer(f"✅ {count} ta foydalanuvchiga yuborildi!", reply_markup=get_admin_keyboard())

async def start_webapp():
    from aiohttp import web
    import os
    
    webapp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webapp')
    
    async def index_handler(request):
        index_file = os.path.join(webapp_dir, 'index.html')
        if os.path.exists(index_file):
            return web.FileResponse(index_file)
        return web.Response(text="Bot is running!", content_type="text/html")
    
    # Healthcheck uchun (serverlar sog'liq tekshiradi)
    async def health_handler(request):
        return web.Response(text="OK")
        
    app = web.Application()
    app.router.add_get('/health', health_handler)
    # WebApp statik fayllarni serve qilish (index.html, style.css, app.js, images/)
    app.router.add_get('/', index_handler)
    app.router.add_static('/', webapp_dir)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"[WEB] Server {port}-portda ishga tushdi")

async def main():
    await db.connect()
    try:
        print("Bot ishga tushdi...")
        # Oldingi webhook ni o'chirish (conflict xatosini oldini olish)
        await bot.delete_webhook(drop_pending_updates=True)
        # WebApp serverni orqa fonda ishga tushirish
        asyncio.create_task(start_webapp())
        await dp.start_polling(bot)
    finally:
        await db.close()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except (KeyboardInterrupt, SystemExit):
            print("Bot to'xtatildi (KeyboardInterrupt).")
            break
        except Exception as e:
            print(f"Tarmoq xatosi yoki uzilish yuz berdi: {e}")
            print("Bot 3 soniyadan so'ng qayta ishga tushadi...")
            import time
            time.sleep(3)
