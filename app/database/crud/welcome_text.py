import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import WelcomeText

logger = logging.getLogger(__name__)

WELCOME_TEXT_KEY = "welcome_text"

async def get_active_welcome_text(db: AsyncSession) -> Optional[str]:
    result = await db.execute(
        select(WelcomeText)
        .where(WelcomeText.is_active == True)
        .order_by(WelcomeText.updated_at.desc())
    )
    welcome_text = result.scalar_one_or_none()
    
    if welcome_text:
        return welcome_text.text_content
    
    return None

async def set_welcome_text(db: AsyncSession, text_content: str, admin_id: int) -> bool:
    try:
        await db.execute(
            update(WelcomeText).values(is_active=False)
        )
        
        new_welcome_text = WelcomeText(
            text_content=text_content,
            is_active=True,
            created_by=admin_id
        )
        
        db.add(new_welcome_text)
        await db.commit()
        await db.refresh(new_welcome_text)
        
        logger.info(f"Установлен новый приветственный текст администратором {admin_id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при установке приветственного текста: {e}")
        await db.rollback()
        return False

async def get_current_welcome_text_or_default() -> str:
    return (
        f"Привет, {{user_name}}! 🎁 3 дней VPN бесплатно! "
        f"Подключайтесь за минуту и забудьте о блокировках. "
        f"✅ До 1 Гбит/с скорость "
        f"✅ Умный VPN — можно не отключать для большинства российских сервисов "
        f"✅ Современные протоколы — максимум защиты и анонимности "
        f"👉 Всего 99₽/мес за 1 устройство "
        f"👇 Жмите кнопку и подключайтесь!"
    )

def replace_placeholders(text: str, user) -> str:
    first_name = getattr(user, 'first_name', None)
    username = getattr(user, 'username', None)
    
    first_name = first_name.strip() if first_name else None
    username = username.strip() if username else None
    
    user_name = first_name or username or "друг"
    display_first_name = first_name or "друг"
    display_username = f"@{username}" if username else (first_name or "друг")
    clean_username = username or first_name or "друг"
    
    replacements = {
        '{user_name}': user_name,
        '{first_name}': display_first_name, 
        '{username}': display_username,
        '{username_clean}': clean_username,
        'Egor': user_name  
    }
    
    result = text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    return result

async def get_welcome_text_for_user(db: AsyncSession, user) -> str:
    welcome_text = await get_active_welcome_text(db)
    
    if not welcome_text:
        welcome_text = await get_current_welcome_text_or_default()
    
    if isinstance(user, str):
        class SimpleUser:
            def __init__(self, name):
                self.first_name = name
                self.username = None
        user = SimpleUser(user)
    
    return replace_placeholders(welcome_text, user)

def get_available_placeholders() -> dict:
    return {
        '{user_name}': 'Имя или username пользователя (приоритет: имя → username → "друг")',
        '{first_name}': 'Только имя пользователя (или "друг" если не указано)',
        '{username}': 'Username с символом @ (или имя если username не указан)',
        '{username_clean}': 'Username без символа @ (или имя если username не указан)'
    }
