import logging
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime
from aiogram import Bot
from aiogram.types import LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.yookassa_service import YooKassaService
from app.database.crud.yookassa import create_yookassa_payment, link_yookassa_payment_to_transaction
from app.database.crud.transaction import create_transaction
from app.database.crud.user import add_user_balance
from app.database.models import TransactionType, PaymentMethod

logger = logging.getLogger(__name__)


class PaymentService:
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self.yookassa_service = YooKassaService() if settings.is_yookassa_enabled() else None
    
    async def create_stars_invoice(
        self,
        amount_kopeks: int,
        description: str,
        payload: Optional[str] = None
    ) -> str:
        
        if not self.bot:
            raise ValueError("Bot instance required for Stars payments")
        
        try:
            stars_amount = max(1, amount_kopeks // 100)
            
            invoice_link = await self.bot.create_invoice_link(
                title="Пополнение баланса VPN",
                description=description,
                payload=payload or f"balance_topup_{amount_kopeks}",
                provider_token="", 
                currency="XTR", 
                prices=[LabeledPrice(label="Пополнение", amount=stars_amount)]
            )
            
            logger.info(f"Создан Stars invoice на {stars_amount} звезд")
            return invoice_link
            
        except Exception as e:
            logger.error(f"Ошибка создания Stars invoice: {e}")
            raise
    
    async def create_yookassa_payment(
        self,
        db: AsyncSession,
        user_id: int,
        amount_kopeks: int,
        description: str,
        receipt_email: Optional[str] = None,
        receipt_phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        
        if not self.yookassa_service:
            logger.error("YooKassa сервис не инициализирован")
            return None
        
        try:
            amount_rubles = amount_kopeks / 100
            
            payment_metadata = metadata or {}
            payment_metadata.update({
                "user_id": str(user_id),
                "amount_kopeks": str(amount_kopeks),
                "type": "balance_topup"
            })
            
            yookassa_response = await self.yookassa_service.create_payment(
                amount=amount_rubles,
                currency="RUB",
                description=description,
                metadata=payment_metadata,
                receipt_email=receipt_email,
                receipt_phone=receipt_phone
            )
            
            if not yookassa_response or yookassa_response.get("error"):
                logger.error(f"Ошибка создания платежа YooKassa: {yookassa_response}")
                return None
            
            yookassa_created_at = None
            if yookassa_response.get("created_at"):
                try:
                    dt_with_tz = datetime.fromisoformat(
                        yookassa_response["created_at"].replace('Z', '+00:00')
                    )
                    yookassa_created_at = dt_with_tz.replace(tzinfo=None)
                except Exception as e:
                    logger.warning(f"Не удалось парсить created_at: {e}")
                    yookassa_created_at = None
            
            local_payment = await create_yookassa_payment(
                db=db,
                user_id=user_id,
                yookassa_payment_id=yookassa_response["id"],
                amount_kopeks=amount_kopeks,
                currency="RUB",
                description=description,
                status=yookassa_response["status"],
                confirmation_url=yookassa_response.get("confirmation_url"),
                metadata_json=payment_metadata,
                payment_method_type=None, 
                yookassa_created_at=yookassa_created_at, 
                test_mode=yookassa_response.get("test_mode", False)
            )
            
            logger.info(f"Создан платеж YooKassa {yookassa_response['id']} на {amount_rubles}₽ для пользователя {user_id}")
            
            return {
                "local_payment_id": local_payment.id,
                "yookassa_payment_id": yookassa_response["id"],
                "confirmation_url": yookassa_response.get("confirmation_url"),
                "amount_kopeks": amount_kopeks,
                "amount_rubles": amount_rubles,
                "status": yookassa_response["status"],
                "created_at": local_payment.created_at
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания платежа YooKassa: {e}")
            return None

    async def process_tribute_payment(
        self, 
        db: AsyncSession, 
        user_id: int, 
        amount_kopeks: int, 
        payment_id: str
    ) -> bool:
        
        try:
            logger.info(f"Обработка Tribute платежа: user_id={user_id}, amount={amount_kopeks} коп., payment_id={payment_id}")
            
            from app.database.crud.user import UserCRUD
            user_crud = UserCRUD()
            
            user = await user_crud.get_user(db, user_id)
            if not user:
                logger.error(f"Пользователь {user_id} не найден для обработки Tribute платежа")
                return False
            
            from app.database.crud.transaction import TransactionCRUD
            transaction_crud = TransactionCRUD()
            
            existing_transaction = await transaction_crud.get_transaction_by_external_id(
                db, f"tribute_{payment_id}"
            )
            
            if existing_transaction:
                logger.info(f"Платеж {payment_id} уже был обработан ранее")
                return True
            
            transaction_data = {
                "user_id": user_id,
                "amount_kopeks": amount_kopeks,
                "transaction_type": "top_up",
                "status": "completed",
                "external_id": f"tribute_{payment_id}",
                "payment_system": "tribute",
                "description": f"Пополнение через Tribute: {payment_id}"
            }
            
            transaction = await transaction_crud.create_transaction(db, transaction_data)
            
            if not transaction:
                logger.error(f"Не удалось создать транзакцию для Tribute платежа {payment_id}")
                return False
            
            success = await user_crud.add_balance(db, user_id, amount_kopeks)
            
            if not success:
                logger.error(f"Не удалось пополнить баланс пользователя {user_id}")
                await transaction_crud.update_transaction_status(db, transaction.id, "failed")
                return False
            
            try:
                from app.localization.texts import get_text
                
                amount_rubles = amount_kopeks / 100
                message = get_text("payment_success_tribute").format(
                    amount=f"{amount_rubles:.2f}",
                    payment_id=payment_id
                )
                
                if hasattr(self, 'bot') and self.bot:
                    await self.bot.send_message(user_id, message)
                
            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление о платеже пользователю {user_id}: {e}")
            
            logger.info(f"✅ Успешно обработан Tribute платеж {payment_id} для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки Tribute платежа {payment_id}: {e}", exc_info=True)
            return False
    
    async def process_yookassa_webhook(self, db: AsyncSession, webhook_data: dict) -> bool:
        try:
            from app.database.crud.yookassa import (
                get_yookassa_payment_by_id, 
                update_yookassa_payment_status,
                link_yookassa_payment_to_transaction
            )
            from app.database.crud.transaction import create_transaction
            from app.database.models import TransactionType, PaymentMethod
            
            payment_object = webhook_data.get("object", {})
            yookassa_payment_id = payment_object.get("id")
            status = payment_object.get("status")
            paid = payment_object.get("paid", False)
            
            if not yookassa_payment_id:
                logger.error("Webhook без ID платежа")
                return False
            
            payment = await get_yookassa_payment_by_id(db, yookassa_payment_id)
            if not payment:
                logger.error(f"Платеж не найден в БД: {yookassa_payment_id}")
                return False
            
            captured_at = None
            if status == "succeeded":
                captured_at = datetime.utcnow() 
            
            updated_payment = await update_yookassa_payment_status(
                db, 
                yookassa_payment_id, 
                status, 
                is_paid=paid,
                is_captured=(status == "succeeded"),
                captured_at=captured_at,
                payment_method_type=payment_object.get("payment_method", {}).get("type")
            )
            
            if status == "succeeded" and paid and not updated_payment.transaction_id:
                transaction = await create_transaction(
                    db,
                    user_id=updated_payment.user_id,
                    type=TransactionType.DEPOSIT, 
                    amount_kopeks=updated_payment.amount_kopeks,
                    description=f"Пополнение через YooKassa ({yookassa_payment_id[:8]}...)",
                    payment_method=PaymentMethod.YOOKASSA,
                    external_id=yookassa_payment_id,
                    is_completed=True
                )
                
                await link_yookassa_payment_to_transaction(
                    db, yookassa_payment_id, transaction.id
                )
                
                from app.database.crud.user import add_user_balance
                await add_user_balance(db, updated_payment.user_id, updated_payment.amount_kopeks)
                
                if self.bot:
                    try:
                        await self.bot.send_message(
                            updated_payment.user.telegram_id,
                            f"✅ <b>Пополнение успешно!</b>\n\n"
                            f"💰 Сумма: {settings.format_price(updated_payment.amount_kopeks)}\n"
                            f"🏦 Способ: Банковская карта\n"
                            f"🆔 Транзакция: {yookassa_payment_id[:8]}...\n\n"
                            f"Баланс пополнен автоматически!",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления о пополнении: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки YooKassa webhook: {e}", exc_info=True)
            return False
    
    async def _process_successful_yookassa_payment(
        self,
        db: AsyncSession,
        payment: "YooKassaPayment"
    ) -> bool:
        
        try:
            transaction = await create_transaction(
                db=db,
                user_id=payment.user_id,
                transaction_type=TransactionType.DEPOSIT,
                amount_kopeks=payment.amount_kopeks,
                description=f"Пополнение через YooKassa: {payment.description}",
                payment_method=PaymentMethod.YOOKASSA,
                external_id=payment.yookassa_payment_id,
                is_completed=True
            )
            
            await link_yookassa_payment_to_transaction(
                db=db,
                yookassa_payment_id=payment.yookassa_payment_id,
                transaction_id=transaction.id
            )
            
            await add_user_balance(db, payment.user_id, payment.amount_kopeks)
            
            logger.info(f"Успешно обработан платеж YooKassa {payment.yookassa_payment_id}: "
                       f"пользователь {payment.user_id} получил {payment.amount_kopeks/100}₽")
            
            if self.bot:
                try:
                    await self._send_payment_success_notification(
                        payment.user.telegram_id, 
                        payment.amount_kopeks
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления о платеже: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки успешного платежа YooKassa {payment.yookassa_payment_id}: {e}")
            return False
    
    async def _send_payment_success_notification(
        self,
        telegram_id: int,
        amount_kopeks: int
    ) -> None:
        
        if not self.bot:
            return
        
        try:
            message = (f"✅ <b>Платеж успешно завершен!</b>\n\n"
                      f"💰 Сумма: {settings.format_price(amount_kopeks)}\n"
                      f"💳 Способ: Банковская карта (YooKassa)\n\n"
                      f"Средства зачислены на ваш баланс!")
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {telegram_id}: {e}")
    
    async def create_tribute_payment(
        self,
        amount_kopeks: int,
        user_id: int,
        description: str
    ) -> str:
        
        if not settings.TRIBUTE_ENABLED:
            raise ValueError("Tribute payments are disabled")
        
        try:
            payment_data = {
                "amount": amount_kopeks,
                "currency": "RUB",
                "description": description,
                "user_id": user_id,
                "callback_url": f"{settings.WEBHOOK_URL}/tribute/callback"
            }
            
            payment_url = f"https://tribute.ru/pay?amount={amount_kopeks}&user={user_id}"
            
            logger.info(f"Создан Tribute платеж на {amount_kopeks/100}₽ для пользователя {user_id}")
            return payment_url
            
        except Exception as e:
            logger.error(f"Ошибка создания Tribute платежа: {e}")
            raise
    
    def verify_tribute_webhook(
        self,
        data: dict,
        signature: str
    ) -> bool:
        
        if not settings.TRIBUTE_WEBHOOK_SECRET:
            return False
        
        try:
            message = str(data).encode()
            expected_signature = hmac.new(
                settings.TRIBUTE_WEBHOOK_SECRET.encode(),
                message,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Ошибка проверки Tribute webhook: {e}")
            return False
    
    async def process_successful_payment(
        self,
        payment_id: str,
        amount_kopeks: int,
        user_id: int,
        payment_method: str
    ) -> bool:
        
        try:
            logger.info(f"Обработан успешный платеж: {payment_id}, {amount_kopeks/100}₽, {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки платежа: {e}")
            return False
