import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.config import settings
from app.database.database import get_db
from app.services.monitoring_service import monitoring_service
from app.utils.decorators import admin_required
from app.utils.pagination import paginate_list
from app.keyboards.admin import (
    get_monitoring_keyboard,
    get_admin_main_keyboard,
    get_monitoring_notification_settings_keyboard,
)
from app.localization.texts import get_texts
from app.services.notification_settings_service import NotificationSettingsService
from app.states import NotificationSettingsStates

logger = logging.getLogger(__name__)
router = Router()


def _format_notification_settings_text(settings_data: dict) -> str:
    def status(flag: bool) -> str:
        return "🟢 Вкл" if flag else "🔴 Выкл"

    return (
        "🔔 <b>Настройки автоматических уведомлений</b>\n\n"
        "🧪 <b>Тестовый период:</b>\n"
        f"• 1 час без подключения: {status(settings_data.get('trial_inactive_1h_enabled'))}\n"
        f"• 24 часа без подключения: {status(settings_data.get('trial_inactive_24h_enabled'))}\n\n"
        "📅 <b>После окончания подписки:</b>\n"
        f"• 1 день после истечения: {status(settings_data.get('expired_day1_enabled'))}\n"
        f"• 2-3 дня: {status(settings_data.get('expired_day23_enabled'))}"
        f" — скидка {settings_data.get('expired_day23_discount_percent', 0)}%"
        f" на {settings_data.get('expired_day23_valid_hours', 0)} ч.\n"
        f"• N дней (от {settings_data.get('expired_dayn_threshold_days', 0)}):"
        f" {status(settings_data.get('expired_dayn_enabled'))}"
        f" — скидка {settings_data.get('expired_dayn_discount_percent', 0)}%"
        f" на {settings_data.get('expired_dayn_valid_hours', 0)} ч.\n\n"
        "Нажмите на кнопки ниже для переключения или изменения параметров."
    )


def _get_notification_settings_view() -> tuple[str, 'InlineKeyboardMarkup']:
    settings_data = NotificationSettingsService.get_all()
    return (
        _format_notification_settings_text(settings_data),
        get_monitoring_notification_settings_keyboard(settings_data),
    )


async def _toggle_notification_setting(
    callback: CallbackQuery,
    getter: Callable[[], bool],
    setter: Callable[[bool], bool],
    label: str,
) -> None:
    new_value = not getter()
    if setter(new_value):
        await callback.answer(f"{label}: {'включено' if new_value else 'отключено'}")
        text, keyboard = _get_notification_settings_view()
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await callback.answer("❌ Не удалось сохранить настройку", show_alert=True)


@router.callback_query(F.data == "admin_monitoring")
@admin_required
async def admin_monitoring_menu(callback: CallbackQuery):
    try:
        async for db in get_db():
            status = await monitoring_service.get_monitoring_status(db)
            
            running_status = "🟢 Работает" if status['is_running'] else "🔴 Остановлен"
            last_update = status['last_update'].strftime('%H:%M:%S') if status['last_update'] else "Никогда"
            
            text = f"""
🔍 <b>Система мониторинга</b>

📊 <b>Статус:</b> {running_status}
🕐 <b>Последнее обновление:</b> {last_update}
⚙️ <b>Интервал проверки:</b> {settings.MONITORING_INTERVAL} мин

📈 <b>Статистика за 24 часа:</b>
• Всего событий: {status['stats_24h']['total_events']}
• Успешных: {status['stats_24h']['successful']}
• Ошибок: {status['stats_24h']['failed']}
• Успешность: {status['stats_24h']['success_rate']}%

🔧 Выберите действие:
"""
            
            keyboard = get_monitoring_keyboard()
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            break
            
    except Exception as e:
        logger.error(f"Ошибка в админ меню мониторинга: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)


@router.callback_query(F.data == "admin_mon_start")
@admin_required
async def start_monitoring_callback(callback: CallbackQuery):
    try:
        if monitoring_service.is_running:
            await callback.answer("ℹ️ Мониторинг уже запущен")
            return
        
        if not monitoring_service.bot:
            monitoring_service.bot = callback.bot
        
        asyncio.create_task(monitoring_service.start_monitoring())
        
        await callback.answer("✅ Мониторинг запущен!")
        
        await admin_monitoring_menu(callback)
        
    except Exception as e:
        logger.error(f"Ошибка запуска мониторинга: {e}")
        await callback.answer(f"❌ Ошибка запуска: {str(e)}", show_alert=True)


@router.callback_query(F.data == "admin_mon_stop")
@admin_required
async def stop_monitoring_callback(callback: CallbackQuery):
    try:
        if not monitoring_service.is_running:
            await callback.answer("ℹ️ Мониторинг уже остановлен")
            return
        
        monitoring_service.stop_monitoring()
        await callback.answer("⏹️ Мониторинг остановлен!")
        
        await admin_monitoring_menu(callback)
        
    except Exception as e:
        logger.error(f"Ошибка остановки мониторинга: {e}")
        await callback.answer(f"❌ Ошибка остановки: {str(e)}", show_alert=True)


@router.callback_query(F.data == "admin_mon_force_check")
@admin_required
async def force_check_callback(callback: CallbackQuery):
    try:
        await callback.answer("⏳ Выполняем проверку подписок...")
        
        async for db in get_db():
            results = await monitoring_service.force_check_subscriptions(db)
            
            text = f"""
✅ <b>Принудительная проверка завершена</b>

📊 <b>Результаты проверки:</b>
• Истекших подписок: {results['expired']}
• Истекающих подписок: {results['expiring']}
• Готовых к автооплате: {results['autopay_ready']}

🕐 <b>Время проверки:</b> {datetime.now().strftime('%H:%M:%S')}

Нажмите "Назад" для возврата в меню мониторинга.
"""
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_monitoring")]
            ])
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            break
            
    except Exception as e:
        logger.error(f"Ошибка принудительной проверки: {e}")
        await callback.answer(f"❌ Ошибка проверки: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("admin_mon_logs"))
@admin_required
async def monitoring_logs_callback(callback: CallbackQuery):
    try:
        page = 1
        if "_page_" in callback.data:
            page = int(callback.data.split("_page_")[1])
        
        async for db in get_db():
            all_logs = await monitoring_service.get_monitoring_logs(db, limit=1000)
            
            if not all_logs:
                text = "📋 <b>Логи мониторинга пусты</b>\n\nСистема еще не выполнила проверки."
                keyboard = get_monitoring_logs_back_keyboard()
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                return
            
            per_page = 8
            paginated_logs = paginate_list(all_logs, page=page, per_page=per_page)
            
            text = f"📋 <b>Логи мониторинга</b> (стр. {page}/{paginated_logs.total_pages})\n\n"
            
            for log in paginated_logs.items:
                icon = "✅" if log['is_success'] else "❌"
                time_str = log['created_at'].strftime('%m-%d %H:%M')
                event_type = log['event_type'].replace('_', ' ').title()
                
                message = log['message']
                if len(message) > 45:
                    message = message[:45] + "..."
                
                text += f"{icon} <code>{time_str}</code> {event_type}\n"
                text += f"   📄 {message}\n\n"
            
            total_success = sum(1 for log in all_logs if log['is_success'])
            total_failed = len(all_logs) - total_success
            success_rate = round(total_success / len(all_logs) * 100, 1) if all_logs else 0
            
            text += f"📊 <b>Общая статистика:</b>\n"
            text += f"• Всего событий: {len(all_logs)}\n"
            text += f"• Успешных: {total_success}\n"
            text += f"• Ошибок: {total_failed}\n"
            text += f"• Успешность: {success_rate}%"
            
            keyboard = get_monitoring_logs_keyboard(page, paginated_logs.total_pages)
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            break
            
    except Exception as e:
        logger.error(f"Ошибка получения логов: {e}")
        await callback.answer("❌ Ошибка получения логов", show_alert=True)


@router.callback_query(F.data == "admin_mon_clear_logs")
@admin_required
async def clear_logs_callback(callback: CallbackQuery):
    try:
        async for db in get_db():
            deleted_count = await monitoring_service.cleanup_old_logs(db, days=0) 
            
            if deleted_count > 0:
                await callback.answer(f"🗑️ Удалено {deleted_count} записей логов")
            else:
                await callback.answer("ℹ️ Логи уже пусты")
            
            await monitoring_logs_callback(callback)
            break
            
    except Exception as e:
        logger.error(f"Ошибка очистки логов: {e}")
        await callback.answer(f"❌ Ошибка очистки: {str(e)}", show_alert=True)


@router.callback_query(F.data == "admin_mon_toggle_notifications")
@admin_required
async def monitoring_notifications_menu(callback: CallbackQuery):
    try:
        text, keyboard = _get_notification_settings_view()
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка отображения настроек уведомлений: {e}")
        await callback.answer("❌ Не удалось получить настройки", show_alert=True)


@router.callback_query(F.data == "admin_mon_test_notifications")
@admin_required
async def test_notifications_callback(callback: CallbackQuery):
    try:
        test_message = f"""
🧪 <b>Тестовое уведомление системы мониторинга</b>

Это тестовое сообщение для проверки работы системы уведомлений.

📊 <b>Статус системы:</b>
• Мониторинг: {'🟢 Работает' if monitoring_service.is_running else '🔴 Остановлен'}
• Уведомления: {'🟢 Включены' if settings.ENABLE_NOTIFICATIONS else '🔴 Отключены'}
• Время теста: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}

✅ Если вы получили это сообщение, система уведомлений работает корректно!
"""
        
        await callback.bot.send_message(
            callback.from_user.id,
            test_message,
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Тестовое уведомление отправлено!")
        
    except Exception as e:
        logger.error(f"Ошибка отправки тестового уведомления: {e}")
        await callback.answer(f"❌ Ошибка отправки: {str(e)}", show_alert=True)


@router.callback_query(F.data == "admin_mon_toggle_notif_trial1h")
@admin_required
async def toggle_trial_1h_notification(callback: CallbackQuery):
    await _toggle_notification_setting(
        callback,
        NotificationSettingsService.is_trial_inactive_1h_enabled,
        NotificationSettingsService.set_trial_inactive_1h_enabled,
        "Триал 1ч",
    )


@router.callback_query(F.data == "admin_mon_toggle_notif_trial24h")
@admin_required
async def toggle_trial_24h_notification(callback: CallbackQuery):
    await _toggle_notification_setting(
        callback,
        NotificationSettingsService.is_trial_inactive_24h_enabled,
        NotificationSettingsService.set_trial_inactive_24h_enabled,
        "Триал 24ч",
    )


@router.callback_query(F.data == "admin_mon_toggle_notif_expired_day1")
@admin_required
async def toggle_expired_day1_notification(callback: CallbackQuery):
    await _toggle_notification_setting(
        callback,
        NotificationSettingsService.is_expired_day1_enabled,
        NotificationSettingsService.set_expired_day1_enabled,
        "Истекла 1 день",
    )


@router.callback_query(F.data == "admin_mon_toggle_notif_expired_day23")
@admin_required
async def toggle_expired_day23_notification(callback: CallbackQuery):
    await _toggle_notification_setting(
        callback,
        NotificationSettingsService.is_expired_day23_enabled,
        NotificationSettingsService.set_expired_day23_enabled,
        "Истекла 2-3 дня",
    )


@router.callback_query(F.data == "admin_mon_toggle_notif_expired_dayn")
@admin_required
async def toggle_expired_dayn_notification(callback: CallbackQuery):
    await _toggle_notification_setting(
        callback,
        NotificationSettingsService.is_expired_dayn_enabled,
        NotificationSettingsService.set_expired_dayn_enabled,
        "Истекла N дней",
    )


async def _start_waiting_for_value(
    callback: CallbackQuery,
    state: FSMContext,
    param: str,
    prompt: str,
) -> None:
    await state.set_state(NotificationSettingsStates.waiting_for_value)
    await state.update_data(param=param)
    await callback.message.answer(prompt)
    await callback.answer()


@router.callback_query(F.data == "admin_mon_edit_notif_day23_discount")
@admin_required
async def edit_day23_discount(callback: CallbackQuery, state: FSMContext):
    await _start_waiting_for_value(
        callback,
        state,
        "day23_discount",
        "Введите новую скидку для уведомления на 2-3 день (%).",
    )


@router.callback_query(F.data == "admin_mon_edit_notif_day23_valid")
@admin_required
async def edit_day23_valid(callback: CallbackQuery, state: FSMContext):
    await _start_waiting_for_value(
        callback,
        state,
        "day23_valid",
        "Введите срок действия предложения для 2-3 дня (в часах).",
    )


@router.callback_query(F.data == "admin_mon_edit_notif_dayn_discount")
@admin_required
async def edit_dayn_discount(callback: CallbackQuery, state: FSMContext):
    await _start_waiting_for_value(
        callback,
        state,
        "dayn_discount",
        "Введите новую скидку для уведомления после N дней (%).",
    )


@router.callback_query(F.data == "admin_mon_edit_notif_dayn_valid")
@admin_required
async def edit_dayn_valid(callback: CallbackQuery, state: FSMContext):
    await _start_waiting_for_value(
        callback,
        state,
        "dayn_valid",
        "Введите срок действия предложения после N дней (в часах).",
    )


@router.callback_query(F.data == "admin_mon_edit_notif_dayn_threshold")
@admin_required
async def edit_dayn_threshold(callback: CallbackQuery, state: FSMContext):
    await _start_waiting_for_value(
        callback,
        state,
        "dayn_threshold",
        "Введите через сколько дней после окончания отправлять усиленную скидку (минимум 4).",
    )


@router.callback_query(F.data == "admin_mon_statistics")
@admin_required
async def monitoring_statistics_callback(callback: CallbackQuery):
    try:
        async for db in get_db():
            from app.database.crud.subscription import get_subscriptions_statistics
            sub_stats = await get_subscriptions_statistics(db)
            
            mon_status = await monitoring_service.get_monitoring_status(db)
            
            week_ago = datetime.now() - timedelta(days=7)
            week_logs = await monitoring_service.get_monitoring_logs(db, limit=1000)
            week_logs = [log for log in week_logs if log['created_at'] >= week_ago]
            
            week_success = sum(1 for log in week_logs if log['is_success'])
            week_errors = len(week_logs) - week_success
            
            text = f"""
📊 <b>Статистика мониторинга</b>

📱 <b>Подписки:</b>
• Всего: {sub_stats['total_subscriptions']}
• Активных: {sub_stats['active_subscriptions']}
• Тестовых: {sub_stats['trial_subscriptions']}
• Платных: {sub_stats['paid_subscriptions']}

📈 <b>За сегодня:</b>
• Успешных операций: {mon_status['stats_24h']['successful']}
• Ошибок: {mon_status['stats_24h']['failed']}
• Успешность: {mon_status['stats_24h']['success_rate']}%

📊 <b>За неделю:</b>
• Всего событий: {len(week_logs)}
• Успешных: {week_success}
• Ошибок: {week_errors}
• Успешность: {round(week_success/len(week_logs)*100, 1) if week_logs else 0}%

🔧 <b>Система:</b>
• Интервал: {settings.MONITORING_INTERVAL} мин
• Уведомления: {'🟢 Вкл' if getattr(settings, 'ENABLE_NOTIFICATIONS', True) else '🔴 Выкл'}
• Автооплата: {', '.join(map(str, settings.get_autopay_warning_days()))} дней
"""
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_monitoring")]
            ])
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            break
            
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await callback.answer(f"❌ Ошибка получения статистики: {str(e)}", show_alert=True)


@router.message(NotificationSettingsStates.waiting_for_value)
@admin_required
async def notification_setting_value(message: Message, state: FSMContext):
    data = await state.get_data()
    param = data.get("param")
    value_raw = (message.text or "").strip()

    try:
        value_int = int(value_raw)
    except ValueError:
        await message.answer("❌ Введите целое число.")
        return

    if param == "day23_discount":
        success = NotificationSettingsService.set_expired_day23_discount_percent(value_int)
        result_text = "Скидка для уведомлений на 2-3 день обновлена."
    elif param == "day23_valid":
        success = NotificationSettingsService.set_expired_day23_valid_hours(value_int)
        result_text = "Срок действия предложения на 2-3 день обновлён."
    elif param == "dayn_discount":
        success = NotificationSettingsService.set_expired_dayn_discount_percent(value_int)
        result_text = "Скидка для уведомлений после N дней обновлена."
    elif param == "dayn_valid":
        success = NotificationSettingsService.set_expired_dayn_valid_hours(value_int)
        result_text = "Срок действия предложения после N дней обновлён."
    elif param == "dayn_threshold":
        success = NotificationSettingsService.set_expired_dayn_threshold_days(value_int)
        result_text = "Порог дней для усиленной скидки обновлён."
    else:
        success = False
        result_text = "Неизвестный параметр."

    if success:
        await message.answer(f"✅ {result_text}")
        text, keyboard = _get_notification_settings_view()
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        await state.clear()
    else:
        await message.answer("❌ Не удалось сохранить значение. Попробуйте ещё раз.")


def get_monitoring_logs_keyboard(current_page: int, total_pages: int):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = []
    
    if total_pages > 1:
        nav_row = []
        
        if current_page > 1:
            nav_row.append(InlineKeyboardButton(
                text="⬅️", 
                callback_data=f"admin_mon_logs_page_{current_page - 1}"
            ))
        
        nav_row.append(InlineKeyboardButton(
            text=f"{current_page}/{total_pages}", 
            callback_data="current_page"
        ))
        
        if current_page < total_pages:
            nav_row.append(InlineKeyboardButton(
                text="➡️", 
                callback_data=f"admin_mon_logs_page_{current_page + 1}"
            ))
        
        keyboard.append(nav_row)
    
    keyboard.extend([
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_mon_logs"),
            InlineKeyboardButton(text="🗑️ Очистить", callback_data="admin_mon_clear_logs")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_monitoring")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_monitoring_logs_back_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_mon_logs"),
            InlineKeyboardButton(text="🔍 Фильтры", callback_data="admin_mon_logs_filters")
        ],
        [
            InlineKeyboardButton(text="🗑️ Очистить логи", callback_data="admin_mon_clear_logs")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_monitoring")]
    ])


@router.message(Command("monitoring"))
@admin_required
async def monitoring_command(message: Message):
    try:
        async for db in get_db():
            status = await monitoring_service.get_monitoring_status(db)
            
            running_status = "🟢 Работает" if status['is_running'] else "🔴 Остановлен"
            
            text = f"""
🔍 <b>Быстрый статус мониторинга</b>

📊 <b>Статус:</b> {running_status}
📈 <b>События за 24ч:</b> {status['stats_24h']['total_events']}
✅ <b>Успешность:</b> {status['stats_24h']['success_rate']}%

Для подробного управления используйте админ-панель.
"""
            
            await message.answer(text, parse_mode="HTML")
            break
            
    except Exception as e:
        logger.error(f"Ошибка команды /monitoring: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


def register_handlers(dp):
    dp.include_router(router)