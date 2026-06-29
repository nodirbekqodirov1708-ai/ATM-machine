#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import asyncio
import logging
import sqlite3
from datetime import datetime
from typing import List, Optional, Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, Message, InputMediaPhoto, Update
)

# ========== CONFIGURATION ==========
BOT_TOKEN = "8773377723:AAEPmTf-brGR0V-_RnDqIGYI8xaG_vUi_Eo"          # Replace with your bot token
ADMIN_ID = 7986852972                # Replace with your Telegram ID
OWNER_USERNAME = "@envysvoid"      # Replace with your Telegram username
WELCOME_IMAGE_URL = "https://picsum.photos/id/20/800/400"   # Welcome banner

# Social media links
INSTAGRAM_URL = "https://instagram.com/DOUBLEDRIP_STORE"
TIKTOK_URL = "https://tiktok.com/@doubledrip_store"
TELEGRAM_CHANNEL_URL = "https://t.me/doubledripstore"

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========== DATABASE SETUP ==========
class Database:
    def __init__(self, db_name: str = "shop_bot.db"):
        self.db_name = db_name

    def execute(self, query: str, params: tuple = ()) -> Optional[sqlite3.Cursor]:
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except Exception as e:
            logger.error(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result


db = Database()


def init_database() -> None:
    """Initialize database tables"""
    db.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "telegram_id INTEGER UNIQUE, username TEXT, join_date TEXT)"
    )
    db.execute(
        "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "category TEXT, image_url TEXT, name TEXT, price TEXT, sizes TEXT, description TEXT)"
    )
    db.execute(
        "CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER, product_id INTEGER, UNIQUE(user_id, product_id))"
    )
    logger.info("Database initialized successfully")


# ========== FSM STATES ==========
class AddProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_image_url = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_sizes = State()
    waiting_for_description = State()


class DeleteProductStates(StatesGroup):
    waiting_for_product_selection = State()


# ========== KEYBOARDS ==========
def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🛍 Shop", callback_data="shop_menu")],
        [InlineKeyboardButton(text="🛒 My Cart", callback_data="view_cart")],
        [InlineKeyboardButton(text="📞 Contact Support", callback_data="contact_support")],
        [InlineKeyboardButton(text="📱 Our Socials", callback_data="socials")]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_socials_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with social media links"""
    buttons = [
        [InlineKeyboardButton(text="📸 Instagram", url=INSTAGRAM_URL)],
        [InlineKeyboardButton(text="🎵 TikTok", url=TIKTOK_URL)],
        [InlineKeyboardButton(text="📢 Telegram Channel", url=TELEGRAM_CHANNEL_URL)],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_shop_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="👕 Clothes", callback_data="category_clothes")],
        [InlineKeyboardButton(text="👖 Pants", callback_data="category_pants")],
        [InlineKeyboardButton(text="👟 Shoes", callback_data="category_shoes")],
        [InlineKeyboardButton(text="⬅️ Back To Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_navigation_keyboard(category: str, current_index: int, total_products: int,
                                    product_id: int) -> InlineKeyboardMarkup:
    buttons = []
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Previous",
            callback_data=f"prev_{category}_{current_index - 1}"
        ))
    if current_index < total_products - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Next",
            callback_data=f"next_{category}_{current_index + 1}"
        ))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([
        InlineKeyboardButton(text="🛒 Add To Cart", callback_data=f"add_to_cart_{product_id}"),
        InlineKeyboardButton(text="💬 Buy Now", callback_data=f"buy_now_{product_id}")
    ])
    buttons.append([InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cart_keyboard(cart_items: List[tuple]) -> InlineKeyboardMarkup:
    buttons = []
    for item in cart_items:
        product_id = item[2] if len(item) > 2 else 0
        product_name = item[3] if len(item) > 3 else f"Product {product_id}"
        buttons.append([InlineKeyboardButton(
            text=f"❌ Remove - {product_name}",
            callback_data=f"remove_from_cart_{product_id}"
        )])
    buttons.append([InlineKeyboardButton(text="🗑 Clear Cart", callback_data="clear_cart")])
    buttons.append([InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Add Product", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="❌ Delete Product", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="📦 View Products", callback_data="admin_view_products")],
        [InlineKeyboardButton(text="📊 Statistics", callback_data="admin_statistics")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_category_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="👕 Clothes", callback_data="cat_clothes")],
        [InlineKeyboardButton(text="👖 Pants", callback_data="cat_pants")],
        [InlineKeyboardButton(text="👟 Shoes", callback_data="cat_shoes")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_products_list_keyboard(products: List[tuple], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    buttons = []
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(products))
    for product in products[start_idx:end_idx]:
        product_id = product[0]
        name = product[3] if len(product) > 3 else "Unknown"
        price = product[4] if len(product) > 4 else "N/A"
        buttons.append([InlineKeyboardButton(
            text=f"{name} - {price}",
            callback_data=f"admin_select_product_{product_id}"
        )])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Previous",
            callback_data=f"admin_products_page_{page - 1}"
        ))
    if end_idx < len(products):
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Next",
            callback_data=f"admin_products_page_{page + 1}"
        ))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])


# ========== BOT INITIALIZATION ==========
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ========== USER HANDLING ==========
async def register_user(user: types.User) -> None:
    user_data = db.fetch_one("SELECT id FROM users WHERE telegram_id = ?", (user.id,))
    if not user_data:
        db.execute(
            "INSERT INTO users (telegram_id, username, join_date) VALUES (?, ?, ?)",
            (user.id, user.username or "No username", datetime.now().isoformat())
        )
        logger.info(f"New user registered: {user.id}")


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ========== BOT COMMANDS ==========
@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await register_user(message.from_user)
    await message.answer_photo(
        photo=WELCOME_IMAGE_URL,
        caption="👋 Welcome to DoubleDripStore!\n\nYour premium destination for fashion and style.",
        reply_markup=get_main_menu_keyboard(is_admin(message.from_user.id))
    )


# ========== MAIN MENU NAVIGATION ==========
@dp.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery) -> None:
    """Return to main menu - properly replaces any message with welcome banner"""
    try:
        if callback.message.photo or callback.message.video or callback.message.animation:
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=WELCOME_IMAGE_URL,
                    caption="👋 Welcome to DoubleDripStore!\n\nYour premium destination for fashion and style."
                ),
                reply_markup=get_main_menu_keyboard(is_admin(callback.from_user.id))
            )
        else:
            try:
                await callback.message.edit_caption(
                    caption="👋 Welcome to DoubleDripStore!\n\nYour premium destination for fashion and style.",
                    reply_markup=get_main_menu_keyboard(is_admin(callback.from_user.id))
                )
            except:
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=WELCOME_IMAGE_URL,
                    caption="👋 Welcome to DoubleDripStore!\n\nYour premium destination for fashion and style.",
                    reply_markup=get_main_menu_keyboard(is_admin(callback.from_user.id))
                )
    except Exception as e:
        logger.error(f"Error in main menu: {e}")
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=WELCOME_IMAGE_URL,
            caption="👋 Welcome to DoubleDripStore!\n\nYour premium destination for fashion and style.",
            reply_markup=get_main_menu_keyboard(is_admin(callback.from_user.id))
        )
    await callback.answer()


@dp.callback_query(F.data == "shop_menu")
async def handle_shop_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="🛍 **Shop Categories**\n\nSelect a category to browse products:",
        reply_markup=get_shop_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "contact_support")
async def handle_contact_support(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption=f"📞 **Need Help?**\n\nContact our support team:\n\n{OWNER_USERNAME}",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "socials")
async def handle_socials(callback: CallbackQuery) -> None:
    """Show social media links"""
    await callback.message.edit_caption(
        caption="📱 **Follow Us**\n\nStay updated with our latest drops and news!\n\n"
                "📸 **Instagram**: [@DOUBLEDRIP_STORE](https://instagram.com/DOUBLEDRIP_STORE)\n"
                "🎵 **TikTok**: [@doubledrip_store](https://tiktok.com/@doubledrip_store)\n"
                "📢 **Telegram Channel**: [DoubleDripStore](https://t.me/doubledripstore)",
        reply_markup=get_socials_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== PRODUCT DISPLAY ==========
async def show_products_by_category(callback: CallbackQuery, category: str, page: int = 0) -> None:
    category_map = {
        "clothes": "👕 Clothes",
        "pants": "👖 Pants",
        "shoes": "👟 Shoes"
    }
    db_category = category_map.get(category, "👕 Clothes")
    products = db.fetch_all(
        "SELECT id, name, price, sizes, description, image_url FROM products WHERE category = ?",
        (db_category,)
    )
    if not products:
        await callback.message.edit_caption(
            caption=f"{db_category}\n\nNo products available in this category.",
            reply_markup=get_shop_menu_keyboard(),
            parse_mode="Markdown"
        )
        return
    if page >= len(products):
        page = 0
    product_id, name, price, sizes, description, image_url = products[page]
    caption = f"**{name}**\n\n💰 Price: {price}\n\n📏 Sizes:\n{sizes}\n\n📝 Description:\n{description}"
    try:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image_url, caption=caption, parse_mode="Markdown"),
            reply_markup=get_product_navigation_keyboard(category, page, len(products), product_id)
        )
    except Exception as e:
        logger.error(f"Error showing product: {e}")
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=get_product_navigation_keyboard(category, page, len(products), product_id),
            parse_mode="Markdown"
        )


@dp.callback_query(F.data.startswith("category_"))
async def handle_category(callback: CallbackQuery) -> None:
    category = callback.data.replace("category_", "")
    await show_products_by_category(callback, category, 0)


@dp.callback_query(F.data.startswith("prev_"))
@dp.callback_query(F.data.startswith("next_"))
async def handle_product_navigation(callback: CallbackQuery) -> None:
    parts = callback.data.split("_", 2)
    if len(parts) >= 3:
        category = parts[1]
        index = int(parts[2])
        await show_products_by_category(callback, category, index)


# ========== BUY NOW ==========
@dp.callback_query(F.data.startswith("buy_now_"))
async def handle_buy_now(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption=f"💬 **To order this product, contact the owner:**\n\n{OWNER_USERNAME}",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== CART SYSTEM ==========
@dp.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("Invalid product", show_alert=True)
        return
    product_id = int(parts[3])
    user = db.fetch_one("SELECT id FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    if not user:
        await callback.answer("Please start the bot first with /start", show_alert=True)
        return
    try:
        db.execute("INSERT INTO cart (user_id, product_id) VALUES (?, ?)", (user[0], product_id))
        await callback.answer("✅ Product added to cart!", show_alert=True)
    except sqlite3.IntegrityError:
        await callback.answer("❌ Product already in cart!", show_alert=True)


@dp.callback_query(F.data == "view_cart")
async def view_cart(callback: CallbackQuery) -> None:
    user = db.fetch_one("SELECT id FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    if not user:
        await callback.answer("Please start the bot first with /start", show_alert=True)
        return
    cart_items = db.fetch_all("""
        SELECT c.id, c.user_id, c.product_id, p.name, p.price, p.image_url
        FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?
    """, (user[0],))
    if not cart_items:
        await callback.message.edit_caption(
            caption="🛒 **Your Cart**\n\nYour cart is empty.",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    total = 0.0
    cart_text = "🛒 **Your Cart**\n\n"
    for item in cart_items:
        name = item[3]
        price = item[4]
        price_str = ''.join(filter(lambda x: x.isdigit() or x == '.', str(price)))
        price_value = float(price_str) if price_str else 0
        total += price_value
        cart_text += f"• **{name}** - {price}\n"
    cart_text += f"\n💰 **Total: ${total:.2f}**"
    first_item = cart_items[0]
    image_url = first_item[5] if len(first_item) > 5 else None
    if image_url:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=image_url, caption=cart_text, parse_mode="Markdown"),
                reply_markup=get_cart_keyboard(cart_items)
            )
        except Exception:
            await callback.message.edit_caption(
                caption=cart_text,
                reply_markup=get_cart_keyboard(cart_items),
                parse_mode="Markdown"
            )
    else:
        await callback.message.edit_caption(
            caption=cart_text,
            reply_markup=get_cart_keyboard(cart_items),
            parse_mode="Markdown"
        )


@dp.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("Invalid product", show_alert=True)
        return
    product_id = int(parts[3])
    user = db.fetch_one("SELECT id FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    if user:
        db.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user[0], product_id))
        await callback.answer("✅ Product removed from cart", show_alert=True)
        await view_cart(callback)


@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery) -> None:
    user = db.fetch_one("SELECT id FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    if user:
        db.execute("DELETE FROM cart WHERE user_id = ?", (user[0],))
        await callback.answer("🗑 Cart cleared!", show_alert=True)
        await view_cart(callback)


# ========== ADMIN PANEL ==========
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.message.edit_caption(
            caption="❌ Access Denied",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        return
    await callback.message.edit_caption(
        caption="👑 **Admin Panel**\n\nWelcome to the administration dashboard.",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== ADMIN - ADD PRODUCT ==========
@dp.callback_query(F.data == "admin_add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.edit_caption(
        caption="➕ **Add New Product**\n\nSelect category:",
        reply_markup=get_category_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddProductStates.waiting_for_category)


@dp.callback_query(AddProductStates.waiting_for_category, F.data.startswith("cat_"))
async def add_product_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.replace("cat_", "")
    category_map = {"clothes": "👕 Clothes", "pants": "👖 Pants", "shoes": "👟 Shoes"}
    await state.update_data(category=category_map[category])
    await callback.message.edit_caption(
        caption="🖼️ **Add New Product**\n\nSend the product image URL:",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddProductStates.waiting_for_image_url)


@dp.message(AddProductStates.waiting_for_image_url)
async def add_product_image_url(message: Message, state: FSMContext) -> None:
    await state.update_data(image_url=message.text)
    await message.answer(
        "✏️ **Add New Product**\n\nEnter product name:",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddProductStates.waiting_for_name)


@dp.message(AddProductStates.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await message.answer(
        "💰 **Add New Product**\n\nEnter product price (e.g., $49.99):",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddProductStates.waiting_for_price)


@dp.message(AddProductStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext) -> None:
    await state.update_data(price=message.text)
    await message.answer(
        "📏 **Add New Product**\n\nEnter available sizes (comma-separated, e.g., S, M, L):",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddProductStates.waiting_for_sizes)


@dp.message(AddProductStates.waiting_for_sizes)
async def add_product_sizes(message: Message, state: FSMContext) -> None:
    await state.update_data(sizes=message.text)
    await message.answer(
        "📝 **Add New Product**\n\nEnter product description:",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddProductStates.waiting_for_description)


@dp.message(AddProductStates.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    db.execute(
        "INSERT INTO products (category, image_url, name, price, sizes, description) VALUES (?, ?, ?, ?, ?, ?)",
        (data['category'], data['image_url'], data['name'], data['price'], data['sizes'], message.text)
    )
    await message.answer(
        "✅ **Product Added Successfully!**\n\nReturning to Admin Panel...",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()


# ========== ADMIN - DELETE PRODUCT ==========
@dp.callback_query(F.data == "admin_delete_product")
async def admin_delete_product(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    products = db.fetch_all("SELECT id, name, price, category FROM products")
    if not products:
        await callback.message.edit_caption(
            caption="❌ **Delete Product**\n\nNo products found.",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    await callback.message.edit_caption(
        caption="❌ **Delete Product**\n\nSelect product to delete:",
        reply_markup=get_products_list_keyboard(products),
        parse_mode="Markdown"
    )
    await state.set_state(DeleteProductStates.waiting_for_product_selection)


@dp.callback_query(DeleteProductStates.waiting_for_product_selection, F.data.startswith("admin_select_product_"))
async def admin_confirm_delete(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("Invalid product", show_alert=True)
        return
    product_id = int(parts[3])
    product = db.fetch_one("SELECT name FROM products WHERE id = ?", (product_id,))
    if product:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        await callback.message.edit_caption(
            caption=f"✅ Product '{product[0]}' has been deleted successfully!",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_caption(
            caption="❌ Product not found!",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="Markdown"
        )
    await state.clear()


@dp.callback_query(F.data.startswith("admin_products_page_"))
async def admin_products_page(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("Invalid page", show_alert=True)
        return
    page = int(parts[3])
    products = db.fetch_all("SELECT id, category, image_url, name, price, sizes, description FROM products")
    await callback.message.edit_caption(
        caption="📦 **Select Product**\n\nChoose a product to delete:",
        reply_markup=get_products_list_keyboard(products, page),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== ADMIN - VIEW PRODUCTS ==========
@dp.callback_query(F.data == "admin_view_products")
async def admin_view_products(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    products = db.fetch_all("SELECT id, category, name, price, sizes FROM products")
    if not products:
        await callback.message.edit_caption(
            caption="📦 **All Products**\n\nNo products found.",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    categories = {}
    for product in products:
        cat = product[1]
        categories.setdefault(cat, []).append(product)
    message_text = "📦 **All Products**\n\n"
    for category, items in categories.items():
        message_text += f"**{category}:**\n"
        for item in items:
            message_text += f"  • {item[2]} - {item[3]} (Sizes: {item[4]})\n"
        message_text += "\n"
    await callback.message.edit_caption(
        caption=message_text,
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== ADMIN - STATISTICS ==========
@dp.callback_query(F.data == "admin_statistics")
async def admin_statistics(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    total_users = db.fetch_one("SELECT COUNT(*) FROM users") or (0,)
    total_products = db.fetch_one("SELECT COUNT(*) FROM products") or (0,)
    total_cart_items = db.fetch_one("SELECT COUNT(*) FROM cart") or (0,)
    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        f"👤 Total Users: {total_users[0]}\n"
        f"📦 Total Products: {total_products[0]}\n"
        f"🛒 Total Cart Items: {total_cart_items[0]}"
    )
    await callback.message.edit_caption(
        caption=stats_text,
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== CATCH-ALL MESSAGE HANDLER ==========
@dp.message()
async def ignore_all_text(message: Message) -> None:
    """Silently ignore any random text messages"""
    pass  # No response


# ========== ERROR HANDLING ==========
@dp.error()
async def error_handler(event: Update, exception: Exception) -> bool:
    """Global error handler for aiogram 3.x"""
    logger.error(f"Error occurred: {exception}", exc_info=True)
    try:
        if event.callback_query:
            await event.callback_query.answer("Something went wrong. Please try again.", show_alert=True)
        elif event.message:
            await event.message.answer("An error occurred. Please try again later.")
    except Exception:
        pass
    return True


# ========== MAIN FUNCTION ==========
async def main() -> None:
    init_database()
    logger.info("DoubleDripStore Bot started successfully!")
    logger.info(f"Admin ID: {ADMIN_ID}")
    logger.info(f"Owner Username: {OWNER_USERNAME}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())