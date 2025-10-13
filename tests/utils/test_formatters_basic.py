"""Тесты для базовых форматтеров из app.utils.formatters."""

from datetime import datetime, timedelta

from app.utils import formatters


def test_format_datetime_handles_iso_strings(fixed_datetime: datetime) -> None:
    """ISO-строка должна корректно преобразовываться в отформатированный текст."""
    iso_value = fixed_datetime.isoformat()
    assert formatters.format_datetime(iso_value) == fixed_datetime.strftime("%d.%m.%Y %H:%M")


def test_format_date_uses_custom_format(fixed_datetime: datetime) -> None:
    """Можно задавать собственный шаблон вывода."""
    iso_value = fixed_datetime.isoformat()
    assert formatters.format_date(iso_value, format_str="%Y/%m/%d") == fixed_datetime.strftime("%Y/%m/%d")


def test_format_time_ago_returns_human_readable_text() -> None:
    """Разница во времени должна переводиться в человеко-понятную строку."""
    point_in_time = datetime.utcnow() - timedelta(minutes=5)
    assert formatters.format_time_ago(point_in_time, language="ru") == "5 мин. назад"
    assert formatters.format_time_ago(point_in_time, language="en") == "5 minutes ago"


def test_format_days_declension_handles_russian_rules() -> None:
    """Склонение дней в русском языке зависит от числа."""
    assert formatters.format_days_declension(1) == "1 день"
    assert formatters.format_days_declension(3) == "3 дня"
    assert formatters.format_days_declension(10) == "10 дней"


def test_format_duration_switches_units() -> None:
    """В зависимости от длины интервала выбирается подходящая единица измерения."""
    assert formatters.format_duration(45) == "45 сек."
    assert formatters.format_duration(120) == "2 мин."
    assert formatters.format_duration(7200) == "2 ч."
    assert formatters.format_duration(172800) == "2 дн."


def test_format_bytes_scales_value() -> None:
    """Размер должен выражаться в наиболее подходящей единице."""
    assert formatters.format_bytes(0) == "0 B"
    assert formatters.format_bytes(1024) == "1 KB"
    assert formatters.format_bytes(1024 * 1024) == "1 MB"


def test_format_percentage_respects_precision() -> None:
    """Проценты форматируются с нужным количеством знаков."""
    assert formatters.format_percentage(12.3456, decimals=2) == "12.35%"


def test_format_number_inserts_separators() -> None:
    """Разделители тысяч должны расставляться корректно как для int, так и для float."""
    assert formatters.format_number(1234567) == "1 234 567"
    assert formatters.format_number(1234.56) == "1 234.55"


def test_truncate_text_appends_suffix() -> None:
    """Строки, превышающие лимит, должны обрезаться и дополняться суффиксом."""
    source = "a" * 10
    assert formatters.truncate_text(source, max_length=5) == "aa..."


def test_format_username_prefers_full_name() -> None:
    """Полное имя имеет приоритет, затем username, затем ID."""
    assert formatters.format_username("nickname", 1, full_name="Имя") == "Имя"
    assert formatters.format_username("nickname", 1, full_name=None) == "@nickname"
    assert formatters.format_username(None, 42, full_name=None) == "ID42"


def test_format_subscription_status_handles_active_and_expired() -> None:
    """Статус подписки различается для активных/просроченных случаев."""
    future = datetime.utcnow() + timedelta(days=2)
    active = formatters.format_subscription_status(
        is_active=True,
        is_trial=False,
        end_date=future,
        language="ru",
    )
    assert active.startswith("✅ Активна")
    assert "(" in active and ")" in active

    past = datetime.utcnow() - timedelta(days=1)
    expired = formatters.format_subscription_status(
        is_active=True,
        is_trial=False,
        end_date=past,
        language="ru",
    )
    assert expired == "⏰ Истекла"


def test_format_traffic_usage_supports_unlimited() -> None:
    """При безлимитном тарифе в строке должна появляться бесконечность."""
    assert formatters.format_traffic_usage(50.0, 0, language="ru") == "50.0 ГБ / ∞"
    assert formatters.format_traffic_usage(10.0, 100, language="ru") == "10.0 ГБ / 100 ГБ (10.0%)"


def test_format_boolean_localises_output() -> None:
    """Булевые значения отображаются локализованными словами."""
    assert formatters.format_boolean(True, language="ru") == "✅ Да"
    assert formatters.format_boolean(False, language="en") == "❌ No"
