import logging
from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import User
from app.states import AdminStates
from app.keyboards.admin import get_welcome_text_keyboard, get_admin_main_keyboard
from app.utils.decorators import admin_required, error_handler
from app.database.crud.welcome_text import (
    get_active_welcome_text, 
    set_welcome_text, 
    get_current_welcome_text_or_default,
    get_available_placeholders
)

logger = logging.getLogger(__name__)

def get_telegram_formatting_info() -> str:
    """Возвращает информацию о поддерживаемом форматировании Telegram"""
    return """
📝 <b>Поддерживаемые теги форматирования:</b>

• <code>&lt;b&gt;жирный текст&lt;/b&gt;</code> → <b>жирный текст</b>
• <code>&lt;i&gt;курсив&lt;/i&gt;</code> → <i>курсив</i>
• <code>&lt;u&gt;подчеркнутый&lt;/u&gt;</code> → <u>подчеркнутый</u>
• <code>&lt;s&gt;зачеркнутый&lt;/s&gt;</code> → <s>зачеркнутый</s>
• <code>&lt;code&gt;моноширинный&lt;/code&gt;</code> → <code>моноширинный</code>
• <code>&lt;pre&gt;блок кода&lt;/pre&gt;</code> → многострочный код
• <code>&lt;a href="https://example.com"&gt;ссылка&lt;/a&gt;</code> → ссылка
• <code>&lt;blockquote&gt;цитата&lt;/blockquote&gt;</code> → ||цитата||

⚠️ <b>ВНИМАНИЕ:</b> Используйте ТОЛЬКО указанные выше теги!
Любые другие HTML-теги не поддерживаются и будут отображаться как обычный текст.

❌ <b>НЕ используйте:</b> <spoiler>, &lt;div&gt;, &lt;span&gt;, &lt;p&gt;, &lt;br&gt;, &lt;h1&gt;-&lt;h6&gt;, &lt;img&gt; и другие HTML-теги.
"""

@admin_required
@error_handler
async def show_welcome_text_panel(
    callback: types.CallbackQuery,
    db_user: User,
    db: AsyncSession
):
    await callback.message.edit_text(
        "👋 Управление приветственным текстом\n\n"
        "Здесь вы можете изменить текст, который показывается новым пользователям после регистрации.\n\n"
        "💡 Доступные плейсхолдеры для автозамены:",
        reply_markup=get_welcome_text_keyboard(db_user.language)
    )
    await callback.answer()

@admin_required
@error_handler
async def show_current_welcome_text(
    callback: types.CallbackQuery,
    db_user: User,
    db: AsyncSession
):
    current_text = await get_active_welcome_text(db)
    
    if not current_text:
        current_text = await get_current_welcome_text_or_default()
        status = "📝 Используется стандартный текст:"
    else:
        status = "📝 Текущий приветственный текст:"
    
    placeholders = get_available_placeholders()
    placeholders_text = "\n".join([f"• <code>{key}</code> - {desc}" for key, desc in placeholders.items()])
    
    await callback.message.edit_text(
        f"{status}\n\n"
        f"<code>{current_text}</code>\n\n"
        f"💡 Доступные плейсхолдеры:\n{placeholders_text}",
        reply_markup=get_welcome_text_keyboard(db_user.language),
        parse_mode="HTML"
    )
    await callback.answer()

@admin_required
@error_handler
async def show_placeholders_help(
    callback: types.CallbackQuery,
    db_user: User,
    db: AsyncSession
):
    placeholders = get_available_placeholders()
    placeholders_text = "\n".join([f"• <code>{key}</code>\n  {desc}" for key, desc in placeholders.items()])
    
    help_text = (
        "💡 Доступные плейсхолдеры для автозамены:\n\n"
        f"{placeholders_text}\n\n"
        "📌 Примеры использования:\n"
        "• <code>Привет, {user_name}! Добро пожаловать!</code>\n"
        "• <code>Здравствуйте, {first_name}! Рады видеть вас!</code>\n"
        "• <code>Привет, {username}! Спасибо за регистрацию!</code>\n\n"
        "При отсутствии данных пользователя используется слово 'друг'."
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_welcome_text_keyboard(db_user.language),
        parse_mode="HTML"
    )
    await callback.answer()

@admin_required
@error_handler
async def show_formatting_help(
    callback: types.CallbackQuery,
    db_user: User,
    db: AsyncSession
):
    formatting_info = get_telegram_formatting_info()
    
    await callback.message.edit_text(
        formatting_info,
        reply_markup=get_welcome_text_keyboard(db_user.language),
        parse_mode="HTML"
    )
    await callback.answer()

@admin_required
@error_handler
async def start_edit_welcome_text(
    callback: types.CallbackQuery,
    state: FSMContext,
    db_user: User,
    db: AsyncSession
):
    current_text = await get_active_welcome_text(db)
    
    if not current_text:
        current_text = await get_current_welcome_text_or_default()
    
    placeholders = get_available_placeholders()
    placeholders_text = "\n".join([f"• <code>{key}</code> - {desc}" for key, desc in placeholders.items()])
    
    await callback.message.edit_text(
        f"📝 Редактирование приветственного текста\n\n"
        f"Текущий текст:\n"
        f"<code>{current_text}</code>\n\n"
        f"💡 Доступные плейсхолдеры:\n{placeholders_text}\n\n"
        f"Отправьте новый текст:",
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.editing_welcome_text)
    await callback.answer()

@admin_required
@error_handler
async def process_welcome_text_edit(
    message: types.Message,
    state: FSMContext,
    db_user: User,
    db: AsyncSession
):
    new_text = message.text.strip()
    
    if len(new_text) < 10:
        await message.answer("❌ Текст слишком короткий! Минимум 10 символов.")
        return
    
    if len(new_text) > 4000:
        await message.answer("❌ Текст слишком длинный! Максимум 4000 символов.")
        return
    
    success = await set_welcome_text(db, new_text, db_user.id)
    
    if success:
        placeholders = get_available_placeholders()
        placeholders_text = "\n".join([f"• <code>{key}</code>" for key in placeholders.keys()])
        
        await message.answer(
            f"✅ Приветственный текст успешно обновлен!\n\n"
            f"Новый текст:\n"
            f"<code>{new_text}</code>\n\n"
            f"💡 Будут заменяться плейсхолдеры: {placeholders_text}",
            reply_markup=get_welcome_text_keyboard(db_user.language),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении текста. Попробуйте еще раз.",
            reply_markup=get_welcome_text_keyboard(db_user.language)
        )
    
    await state.clear()

@admin_required
@error_handler
async def reset_welcome_text(
    callback: types.CallbackQuery,
    db_user: User,
    db: AsyncSession
):
    default_text = await get_current_welcome_text_or_default()
    success = await set_welcome_text(db, default_text, db_user.id)
    
    if success:
        await callback.message.edit_text(
            f"✅ Приветственный текст сброшен на стандартный!\n\n"
            f"Стандартный текст:\n"
            f"<code>{default_text}</code>\n\n"
            f"💡 Плейсхолдер <code>{{user_name}}</code> будет заменяться на имя пользователя",
            reply_markup=get_welcome_text_keyboard(db_user.language),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сбросе текста. Попробуйте еще раз.",
            reply_markup=get_welcome_text_keyboard(db_user.language)
        )
    
    await callback.answer()

@admin_required
@error_handler
async def show_preview_welcome_text(
    callback: types.CallbackQuery,
    db_user: User,
    db: AsyncSession
):
    from app.database.crud.welcome_text import get_welcome_text_for_user
    
    class TestUser:
        def __init__(self):
            self.first_name = "Иван"
            self.username = "test_user"
    
    test_user = TestUser()
    preview_text = await get_welcome_text_for_user(db, test_user)
    
    await callback.message.edit_text(
        f"👁️ Предварительный просмотр\n\n"
        f"Как будет выглядеть текст для пользователя 'Иван' (@test_user):\n\n"
        f"<code>{preview_text}</code>",
        reply_markup=get_welcome_text_keyboard(db_user.language),
        parse_mode="HTML"
    )
    await callback.answer()

def register_welcome_text_handlers(dp: Dispatcher):
    dp.callback_query.register(
        show_welcome_text_panel,
        F.data == "welcome_text_panel"
    )
    
    dp.callback_query.register(
        show_current_welcome_text,
        F.data == "show_welcome_text"
    )
    
    dp.callback_query.register(
        show_placeholders_help,
        F.data == "show_placeholders_help"
    )
    
    dp.callback_query.register(
        show_formatting_help,
        F.data == "show_formatting_help"
    )
    
    dp.callback_query.register(
        show_preview_welcome_text,
        F.data == "preview_welcome_text"
    )
    
    dp.callback_query.register(
        start_edit_welcome_text,
        F.data == "edit_welcome_text"
    )
    
    dp.callback_query.register(
        reset_welcome_text,
        F.data == "reset_welcome_text"
    )
    
    dp.message.register(
        process_welcome_text_edit,
        AdminStates.editing_welcome_text
    )
