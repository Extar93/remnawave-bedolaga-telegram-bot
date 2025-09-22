import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    AdvertisingCampaign,
    AdvertisingCampaignRegistration,
    Transaction,
    TransactionType,
    Subscription,
    User,
)

logger = logging.getLogger(__name__)


async def create_campaign(
    db: AsyncSession,
    *,
    name: str,
    start_parameter: str,
    bonus_type: str,
    created_by: Optional[int] = None,
    balance_bonus_kopeks: int = 0,
    subscription_duration_days: Optional[int] = None,
    subscription_traffic_gb: Optional[int] = None,
    subscription_device_limit: Optional[int] = None,
    subscription_squads: Optional[List[str]] = None,
) -> AdvertisingCampaign:
    campaign = AdvertisingCampaign(
        name=name,
        start_parameter=start_parameter,
        bonus_type=bonus_type,
        balance_bonus_kopeks=balance_bonus_kopeks or 0,
        subscription_duration_days=subscription_duration_days,
        subscription_traffic_gb=subscription_traffic_gb,
        subscription_device_limit=subscription_device_limit,
        subscription_squads=subscription_squads or [],
        created_by=created_by,
        is_active=True,
    )

    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    logger.info(
        "📣 Создана рекламная кампания %s (start=%s, bonus=%s)",
        campaign.name,
        campaign.start_parameter,
        campaign.bonus_type,
    )
    return campaign


async def get_campaign_by_id(
    db: AsyncSession, campaign_id: int
) -> Optional[AdvertisingCampaign]:
    result = await db.execute(
        select(AdvertisingCampaign)
        .options(selectinload(AdvertisingCampaign.registrations))
        .where(AdvertisingCampaign.id == campaign_id)
    )
    return result.scalar_one_or_none()


async def get_campaign_by_start_parameter(
    db: AsyncSession,
    start_parameter: str,
    *,
    only_active: bool = False,
) -> Optional[AdvertisingCampaign]:
    stmt = select(AdvertisingCampaign).where(
        AdvertisingCampaign.start_parameter == start_parameter
    )
    if only_active:
        stmt = stmt.where(AdvertisingCampaign.is_active.is_(True))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_campaigns_list(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 20,
    include_inactive: bool = True,
) -> List[AdvertisingCampaign]:
    stmt = (
        select(AdvertisingCampaign)
        .options(selectinload(AdvertisingCampaign.registrations))
        .order_by(AdvertisingCampaign.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if not include_inactive:
        stmt = stmt.where(AdvertisingCampaign.is_active.is_(True))

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_campaigns_count(
    db: AsyncSession, *, is_active: Optional[bool] = None
) -> int:
    stmt = select(func.count(AdvertisingCampaign.id))
    if is_active is not None:
        stmt = stmt.where(AdvertisingCampaign.is_active.is_(is_active))

    result = await db.execute(stmt)
    return result.scalar_one() or 0


async def update_campaign(
    db: AsyncSession,
    campaign: AdvertisingCampaign,
    **kwargs,
) -> AdvertisingCampaign:
    allowed_fields = {
        "name",
        "start_parameter",
        "bonus_type",
        "balance_bonus_kopeks",
        "subscription_duration_days",
        "subscription_traffic_gb",
        "subscription_device_limit",
        "subscription_squads",
        "is_active",
    }

    update_data = {key: value for key, value in kwargs.items() if key in allowed_fields}

    if not update_data:
        return campaign

    update_data["updated_at"] = datetime.utcnow()

    await db.execute(
        update(AdvertisingCampaign)
        .where(AdvertisingCampaign.id == campaign.id)
        .values(**update_data)
    )
    await db.commit()
    await db.refresh(campaign)

    logger.info("✏️ Обновлена рекламная кампания %s (%s)", campaign.name, update_data)
    return campaign


async def delete_campaign(db: AsyncSession, campaign: AdvertisingCampaign) -> bool:
    await db.execute(
        delete(AdvertisingCampaign).where(AdvertisingCampaign.id == campaign.id)
    )
    await db.commit()
    logger.info("🗑️ Удалена рекламная кампания %s", campaign.name)
    return True


async def record_campaign_registration(
    db: AsyncSession,
    *,
    campaign_id: int,
    user_id: int,
    bonus_type: str,
    balance_bonus_kopeks: int = 0,
    subscription_duration_days: Optional[int] = None,
) -> AdvertisingCampaignRegistration:
    existing = await db.execute(
        select(AdvertisingCampaignRegistration).where(
            and_(
                AdvertisingCampaignRegistration.campaign_id == campaign_id,
                AdvertisingCampaignRegistration.user_id == user_id,
            )
        )
    )
    registration = existing.scalar_one_or_none()
    if registration:
        return registration

    registration = AdvertisingCampaignRegistration(
        campaign_id=campaign_id,
        user_id=user_id,
        bonus_type=bonus_type,
        balance_bonus_kopeks=balance_bonus_kopeks or 0,
        subscription_duration_days=subscription_duration_days,
    )
    db.add(registration)
    await db.commit()
    await db.refresh(registration)

    logger.info("📈 Регистрируем пользователя %s в кампании %s", user_id, campaign_id)
    return registration


async def get_campaign_statistics(
    db: AsyncSession,
    campaign_id: int,
) -> Dict[str, Optional[int]]:
    aggregate_result = await db.execute(
        select(
            func.count(AdvertisingCampaignRegistration.id),
            func.coalesce(
                func.sum(AdvertisingCampaignRegistration.balance_bonus_kopeks), 0
            ),
            func.max(AdvertisingCampaignRegistration.created_at),
        ).where(AdvertisingCampaignRegistration.campaign_id == campaign_id)
    )
    registrations_count, total_balance, last_registration = aggregate_result.one()

    subscription_count_result = await db.execute(
        select(func.count(AdvertisingCampaignRegistration.id)).where(
            and_(
                AdvertisingCampaignRegistration.campaign_id == campaign_id,
                AdvertisingCampaignRegistration.bonus_type == "subscription",
            )
        )
    )

    campaign_users_subquery = (
        select(AdvertisingCampaignRegistration.user_id)
        .where(AdvertisingCampaignRegistration.campaign_id == campaign_id)
    )

    revenue_filter = and_(
        Transaction.user_id.in_(campaign_users_subquery),
        Transaction.is_completed.is_(True),
        Transaction.amount_kopeks > 0,
        Transaction.type.in_(
            [
                TransactionType.DEPOSIT.value,
                TransactionType.SUBSCRIPTION_PAYMENT.value,
            ]
        ),
    )

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount_kopeks), 0)).where(
            revenue_filter
        )
    )
    revenue_kopeks = revenue_result.scalar() or 0

    transactions_count_result = await db.execute(
        select(func.count(Transaction.id)).where(revenue_filter)
    )
    transactions_count = transactions_count_result.scalar() or 0

    paying_users_result = await db.execute(
        select(func.count(func.distinct(Transaction.user_id))).where(
            revenue_filter
        )
    )
    paying_users = paying_users_result.scalar() or 0

    trial_users_result = await db.execute(
        select(func.count(func.distinct(Subscription.user_id))).where(
            and_(
                Subscription.user_id.in_(campaign_users_subquery),
                Subscription.is_trial.is_(True),
            )
        )
    )
    trial_users = trial_users_result.scalar() or 0

    paid_flag_users_result = await db.execute(
        select(func.count(func.distinct(User.id))).where(
            and_(
                User.id.in_(campaign_users_subquery),
                User.has_had_paid_subscription.is_(True),
            )
        )
    )
    paid_flag_users = paid_flag_users_result.scalar() or 0

    registrations = registrations_count or 0
    conversion_base = registrations if registrations > 0 else None
    effective_paying_users = max(paying_users, paid_flag_users or 0)

    conversion_rate = (
        round((effective_paying_users / registrations) * 100, 1)
        if conversion_base
        else 0.0
    )

    trial_conversion_rate = (
        round((effective_paying_users / trial_users) * 100, 1)
        if trial_users
        else 0.0
    )

    avg_revenue_per_user = (
        int(round(revenue_kopeks / registrations)) if registrations else 0
    )
    avg_revenue_per_paying_user = (
        int(round(revenue_kopeks / effective_paying_users))
        if effective_paying_users
        else 0
    )

    return {
        "registrations": registrations,
        "balance_issued": total_balance or 0,
        "subscription_issued": subscription_count_result.scalar() or 0,
        "last_registration": last_registration,
        "revenue_kopeks": revenue_kopeks,
        "transactions_count": transactions_count,
        "paying_users": effective_paying_users,
        "trial_users": trial_users,
        "conversion_rate": conversion_rate,
        "trial_conversion_rate": trial_conversion_rate,
        "avg_revenue_per_user": avg_revenue_per_user,
        "avg_revenue_per_paying_user": avg_revenue_per_paying_user,
    }


async def get_campaign_registration_by_user(
    db: AsyncSession,
    user_id: int,
) -> Optional[AdvertisingCampaignRegistration]:
    result = await db.execute(
        select(AdvertisingCampaignRegistration)
        .options(selectinload(AdvertisingCampaignRegistration.campaign))
        .where(AdvertisingCampaignRegistration.user_id == user_id)
        .order_by(AdvertisingCampaignRegistration.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_campaign_registrations_for_users(
    db: AsyncSession,
    user_ids: List[int],
) -> Dict[int, AdvertisingCampaignRegistration]:
    if not user_ids:
        return {}

    result = await db.execute(
        select(AdvertisingCampaignRegistration)
        .options(selectinload(AdvertisingCampaignRegistration.campaign))
        .where(AdvertisingCampaignRegistration.user_id.in_(user_ids))
    )

    registrations = result.scalars().all()
    return {registration.user_id: registration for registration in registrations}


async def get_campaigns_overview(db: AsyncSession) -> Dict[str, int]:
    total = await get_campaigns_count(db)
    active = await get_campaigns_count(db, is_active=True)
    inactive = await get_campaigns_count(db, is_active=False)

    registrations_result = await db.execute(
        select(func.count(AdvertisingCampaignRegistration.id))
    )

    balance_result = await db.execute(
        select(
            func.coalesce(
                func.sum(AdvertisingCampaignRegistration.balance_bonus_kopeks), 0
            )
        )
    )

    subscription_result = await db.execute(
        select(func.count(AdvertisingCampaignRegistration.id)).where(
            AdvertisingCampaignRegistration.bonus_type == "subscription"
        )
    )

    return {
        "total": total,
        "active": active,
        "inactive": inactive,
        "registrations": registrations_result.scalar() or 0,
        "balance_total": balance_result.scalar() or 0,
        "subscription_total": subscription_result.scalar() or 0,
    }
