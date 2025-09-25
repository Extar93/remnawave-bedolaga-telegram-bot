import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.transaction import get_user_total_spent_kopeks
from app.database.models import PromoGroup, User

logger = logging.getLogger(__name__)


async def _get_best_group_for_spending(
    db: AsyncSession,
    total_spent_kopeks: int,
    min_threshold_kopeks: int = 0,
) -> Optional[PromoGroup]:
    if total_spent_kopeks <= 0:
        return None

    result = await db.execute(
        select(PromoGroup)
        .where(PromoGroup.auto_assign_total_spent_kopeks.is_not(None))
        .where(PromoGroup.auto_assign_total_spent_kopeks > 0)
        .order_by(PromoGroup.auto_assign_total_spent_kopeks.desc(), PromoGroup.id.desc())
    )
    groups = result.scalars().all()

    for group in groups:
        threshold = group.auto_assign_total_spent_kopeks or 0
        if (
            threshold
            and total_spent_kopeks >= threshold
            and threshold > min_threshold_kopeks
        ):
            return group

    return None


async def maybe_assign_promo_group_by_total_spent(
    db: AsyncSession,
    user_id: int,
) -> Optional[PromoGroup]:
    user = await db.get(User, user_id)
    if not user:
        logger.debug("Не удалось найти пользователя %s для автовыдачи промогруппы", user_id)
        return None

    total_spent = await get_user_total_spent_kopeks(db, user_id)
    if total_spent <= 0:
        return None

    previous_threshold = user.auto_promo_group_threshold_kopeks or 0

    target_group = await _get_best_group_for_spending(
        db,
        total_spent,
        min_threshold_kopeks=previous_threshold,
    )
    if not target_group:
        return None

    try:
        previous_group_id = user.promo_group_id
        target_threshold = target_group.auto_assign_total_spent_kopeks or 0

        if target_threshold <= previous_threshold:
            logger.debug(
                "Порог промогруппы '%s' (%s) не превышает ранее назначенный (%s) для пользователя %s",
                target_group.name,
                target_threshold,
                previous_threshold,
                user.telegram_id,
            )
            return None

        if user.auto_promo_group_assigned and target_group.id == previous_group_id:
            logger.debug(
                "Пользователь %s уже находится в актуальной промогруппе '%s', повторная выдача не требуется",
                user.telegram_id,
                target_group.name,
            )
            if target_threshold > previous_threshold:
                user.auto_promo_group_threshold_kopeks = target_threshold
                user.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(user)
            return target_group

        user.auto_promo_group_assigned = True
        user.auto_promo_group_threshold_kopeks = target_threshold
        user.updated_at = datetime.utcnow()

        if target_group.id != previous_group_id:
            user.promo_group_id = target_group.id
            user.promo_group = target_group
            logger.info(
                "🤖 Пользователь %s автоматически переведен в промогруппу '%s' за траты %s ₽",
                user.telegram_id,
                target_group.name,
                total_spent / 100,
            )
        else:
            logger.info(
                "🤖 Пользователь %s уже находится в подходящей промогруппе '%s', отмечаем автоприсвоение",
                user.telegram_id,
                target_group.name,
            )

        await db.commit()
        await db.refresh(user)

        return target_group
    except Exception as exc:
        logger.error(
            "Ошибка при автоматическом назначении промогруппы пользователю %s: %s",
            user_id,
            exc,
        )
        await db.rollback()
        return None
