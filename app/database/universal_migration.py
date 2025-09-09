import logging
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import engine

logger = logging.getLogger(__name__)

async def get_database_type():
    return engine.dialect.name

async def check_table_exists(table_name: str) -> bool:
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            if db_type == 'sqlite':
                result = await conn.execute(text(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """))
                return result.fetchone() is not None
                
            elif db_type == 'postgresql':
                result = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = :table_name
                """), {"table_name": table_name})
                return result.fetchone() is not None
                
            elif db_type == 'mysql':
                result = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = DATABASE() AND table_name = :table_name
                """), {"table_name": table_name})
                return result.fetchone() is not None
                
            return False
            
    except Exception as e:
        logger.error(f"Ошибка проверки существования таблицы {table_name}: {e}")
        return False

async def check_column_exists(table_name: str, column_name: str) -> bool:
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            if db_type == 'sqlite':
                result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = result.fetchall()
                return any(col[1] == column_name for col in columns)
                
            elif db_type == 'postgresql':
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                """), {"table_name": table_name, "column_name": column_name})
                return result.fetchone() is not None
                
            elif db_type == 'mysql':
                result = await conn.execute(text("""
                    SELECT COLUMN_NAME 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_NAME = :table_name 
                    AND COLUMN_NAME = :column_name
                """), {"table_name": table_name, "column_name": column_name})
                return result.fetchone() is not None
                
            return False
            
    except Exception as e:
        logger.error(f"Ошибка проверки существования колонки {column_name}: {e}")
        return False

async def create_yookassa_payments_table():
    
    table_exists = await check_table_exists('yookassa_payments')
    if table_exists:
        logger.info("Таблица yookassa_payments уже существует")
        return True
    
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            if db_type == 'sqlite':
                create_sql = """
                CREATE TABLE yookassa_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    yookassa_payment_id VARCHAR(255) UNIQUE NOT NULL,
                    amount_kopeks INTEGER NOT NULL,
                    currency VARCHAR(3) DEFAULT 'RUB' NOT NULL,
                    description TEXT NULL,
                    status VARCHAR(50) NOT NULL,
                    is_paid BOOLEAN DEFAULT 0,
                    is_captured BOOLEAN DEFAULT 0,
                    confirmation_url TEXT NULL,
                    metadata_json TEXT NULL,
                    transaction_id INTEGER NULL,
                    payment_method_type VARCHAR(50) NULL,
                    refundable BOOLEAN DEFAULT 0,
                    test_mode BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    yookassa_created_at DATETIME NULL,
                    captured_at DATETIME NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                );
                
                CREATE INDEX idx_yookassa_payments_user_id ON yookassa_payments(user_id);
                CREATE INDEX idx_yookassa_payments_yookassa_id ON yookassa_payments(yookassa_payment_id);
                CREATE INDEX idx_yookassa_payments_status ON yookassa_payments(status);
                """
                
            elif db_type == 'postgresql':
                create_sql = """
                CREATE TABLE yookassa_payments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    yookassa_payment_id VARCHAR(255) UNIQUE NOT NULL,
                    amount_kopeks INTEGER NOT NULL,
                    currency VARCHAR(3) DEFAULT 'RUB' NOT NULL,
                    description TEXT NULL,
                    status VARCHAR(50) NOT NULL,
                    is_paid BOOLEAN DEFAULT FALSE,
                    is_captured BOOLEAN DEFAULT FALSE,
                    confirmation_url TEXT NULL,
                    metadata_json JSONB NULL,
                    transaction_id INTEGER NULL,
                    payment_method_type VARCHAR(50) NULL,
                    refundable BOOLEAN DEFAULT FALSE,
                    test_mode BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    yookassa_created_at TIMESTAMP NULL,
                    captured_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                );
                
                CREATE INDEX idx_yookassa_payments_user_id ON yookassa_payments(user_id);
                CREATE INDEX idx_yookassa_payments_yookassa_id ON yookassa_payments(yookassa_payment_id);
                CREATE INDEX idx_yookassa_payments_status ON yookassa_payments(status);
                """
                
            elif db_type == 'mysql':
                create_sql = """
                CREATE TABLE yookassa_payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    yookassa_payment_id VARCHAR(255) UNIQUE NOT NULL,
                    amount_kopeks INT NOT NULL,
                    currency VARCHAR(3) DEFAULT 'RUB' NOT NULL,
                    description TEXT NULL,
                    status VARCHAR(50) NOT NULL,
                    is_paid BOOLEAN DEFAULT FALSE,
                    is_captured BOOLEAN DEFAULT FALSE,
                    confirmation_url TEXT NULL,
                    metadata_json JSON NULL,
                    transaction_id INT NULL,
                    payment_method_type VARCHAR(50) NULL,
                    refundable BOOLEAN DEFAULT FALSE,
                    test_mode BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    yookassa_created_at DATETIME NULL,
                    captured_at DATETIME NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                );
                
                CREATE INDEX idx_yookassa_payments_user_id ON yookassa_payments(user_id);
                CREATE INDEX idx_yookassa_payments_yookassa_id ON yookassa_payments(yookassa_payment_id);
                CREATE INDEX idx_yookassa_payments_status ON yookassa_payments(status);
                """
            else:
                logger.error(f"Неподдерживаемый тип БД для создания таблицы: {db_type}")
                return False
            
            await conn.execute(text(create_sql))
            logger.info("Таблица yookassa_payments успешно создана")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка создания таблицы yookassa_payments: {e}")
        return False

async def create_user_messages_table():
    """Создание таблицы user_messages"""
    table_exists = await check_table_exists('user_messages')
    if table_exists:
        logger.info("Таблица user_messages уже существует")
        return True
    
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            if db_type == 'sqlite':
                create_sql = """
                CREATE TABLE user_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_by INTEGER NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                );
                
                CREATE INDEX idx_user_messages_active ON user_messages(is_active);
                CREATE INDEX idx_user_messages_sort ON user_messages(sort_order, created_at);
                """
                
            elif db_type == 'postgresql':
                create_sql = """
                CREATE TABLE user_messages (
                    id SERIAL PRIMARY KEY,
                    message_text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    sort_order INTEGER DEFAULT 0,
                    created_by INTEGER NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                );
                
                CREATE INDEX idx_user_messages_active ON user_messages(is_active);
                CREATE INDEX idx_user_messages_sort ON user_messages(sort_order, created_at);
                """
                
            elif db_type == 'mysql':
                create_sql = """
                CREATE TABLE user_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message_text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    sort_order INT DEFAULT 0,
                    created_by INT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                );
                
                CREATE INDEX idx_user_messages_active ON user_messages(is_active);
                CREATE INDEX idx_user_messages_sort ON user_messages(sort_order, created_at);
                """
            else:
                logger.error(f"Неподдерживаемый тип БД для создания таблицы: {db_type}")
                return False
            
            await conn.execute(text(create_sql))
            logger.info("Таблица user_messages успешно создана")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка создания таблицы user_messages: {e}")
        return False

async def fix_foreign_keys_for_user_deletion():
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            if db_type == 'postgresql':
                try:
                    await conn.execute(text("""
                        ALTER TABLE user_messages 
                        DROP CONSTRAINT IF EXISTS user_messages_created_by_fkey;
                    """))
                    
                    await conn.execute(text("""
                        ALTER TABLE user_messages 
                        ADD CONSTRAINT user_messages_created_by_fkey 
                        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
                    """))
                    logger.info("Обновлен внешний ключ user_messages.created_by")
                except Exception as e:
                    logger.warning(f"Ошибка обновления FK user_messages: {e}")
                
                try:
                    await conn.execute(text("""
                        ALTER TABLE promocodes 
                        DROP CONSTRAINT IF EXISTS promocodes_created_by_fkey;
                    """))
                    
                    await conn.execute(text("""
                        ALTER TABLE promocodes 
                        ADD CONSTRAINT promocodes_created_by_fkey 
                        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
                    """))
                    logger.info("Обновлен внешний ключ promocodes.created_by")
                except Exception as e:
                    logger.warning(f"Ошибка обновления FK promocodes: {e}")
            
            logger.info("Внешние ключи обновлены для безопасного удаления пользователей")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка обновления внешних ключей: {e}")
        return False

async def add_remnawave_v2_columns():
    
    columns_to_add = {
        'lifetime_used_traffic_bytes': 'BIGINT DEFAULT 0',
        'last_remnawave_sync': 'TIMESTAMP NULL',
        'trojan_password': 'VARCHAR(255) NULL',
        'vless_uuid': 'VARCHAR(255) NULL',
        'ss_password': 'VARCHAR(255) NULL'
    }
    
    logger.info("=== ПРОВЕРКА КОЛОНОК REMNAWAVE V2.1.5 ===")
    
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            columns_added = 0
            
            for column_name, column_def in columns_to_add.items():
                exists = await check_column_exists('users', column_name)
                
                if not exists:
                    logger.info(f"Добавление колонки {column_name} в таблицу users")
                    
                    if db_type == 'sqlite':
                        if column_def.startswith('BIGINT'):
                            column_def = column_def.replace('BIGINT', 'INTEGER')
                        column_def = column_def.replace('TIMESTAMP', 'DATETIME')
                    elif db_type == 'mysql':
                        column_def = column_def.replace('TIMESTAMP', 'DATETIME')
                    
                    try:
                        await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
                        columns_added += 1
                        logger.info(f"Колонка {column_name} успешно добавлена")
                    except Exception as e:
                        logger.error(f"Ошибка добавления колонки {column_name}: {e}")
                        continue
                        
                else:
                    logger.debug(f"Колонка {column_name} уже существует")
            
            if columns_added > 0:
                logger.info(f"Добавлено {columns_added} новых колонок для RemnaWave v2.1.5")
            else:
                logger.info("Все колонки RemnaWave v2.1.5 уже существуют")
                
            return columns_added
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении колонок RemnaWave v2.1.5: {e}")
        return 0

async def add_referral_system_columns():
    logger.info("=== МИГРАЦИЯ РЕФЕРАЛЬНОЙ СИСТЕМЫ ===")
    
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            column_exists = await check_column_exists('users', 'has_made_first_topup')
            
            if not column_exists:
                logger.info("Добавление колонки has_made_first_topup в таблицу users")
                
                if db_type == 'sqlite':
                    column_def = 'BOOLEAN DEFAULT 0'
                else:
                    column_def = 'BOOLEAN DEFAULT FALSE'
                
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN has_made_first_topup {column_def}"))
                logger.info("Колонка has_made_first_topup успешно добавлена")
                
                logger.info("Обновление существующих пользователей...")
                
                if db_type == 'sqlite':
                    update_sql = """
                        UPDATE users 
                        SET has_made_first_topup = 1 
                        WHERE balance_kopeks > 0 OR has_had_paid_subscription = 1
                    """
                else:
                    update_sql = """
                        UPDATE users 
                        SET has_made_first_topup = TRUE 
                        WHERE balance_kopeks > 0 OR has_had_paid_subscription = TRUE
                    """
                
                result = await conn.execute(text(update_sql))
                updated_count = result.rowcount
                
                logger.info(f"Обновлено {updated_count} пользователей с has_made_first_topup = TRUE")
                logger.info("✅ Миграция реферальной системы завершена")
                
                return True
            else:
                logger.info("Колонка has_made_first_topup уже существует")
                return True
                
    except Exception as e:
        logger.error(f"Ошибка миграции реферальной системы: {e}")
        return False

async def create_subscription_conversions_table():
    
    table_exists = await check_table_exists('subscription_conversions')
    if table_exists:
        logger.info("Таблица subscription_conversions уже существует")
        return True
    
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            if db_type == 'sqlite':
                create_sql = """
                CREATE TABLE subscription_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    converted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    trial_duration_days INTEGER NULL,
                    payment_method VARCHAR(50) NULL,
                    first_payment_amount_kopeks INTEGER NULL,
                    first_paid_period_days INTEGER NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                
                CREATE INDEX idx_subscription_conversions_user_id ON subscription_conversions(user_id);
                CREATE INDEX idx_subscription_conversions_converted_at ON subscription_conversions(converted_at);
                """
                
            elif db_type == 'postgresql':
                create_sql = """
                CREATE TABLE subscription_conversions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trial_duration_days INTEGER NULL,
                    payment_method VARCHAR(50) NULL,
                    first_payment_amount_kopeks INTEGER NULL,
                    first_paid_period_days INTEGER NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                
                CREATE INDEX idx_subscription_conversions_user_id ON subscription_conversions(user_id);
                CREATE INDEX idx_subscription_conversions_converted_at ON subscription_conversions(converted_at);
                """
                
            elif db_type == 'mysql':
                create_sql = """
                CREATE TABLE subscription_conversions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    converted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    trial_duration_days INT NULL,
                    payment_method VARCHAR(50) NULL,
                    first_payment_amount_kopeks INT NULL,
                    first_paid_period_days INT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                
                CREATE INDEX idx_subscription_conversions_user_id ON subscription_conversions(user_id);
                CREATE INDEX idx_subscription_conversions_converted_at ON subscription_conversions(converted_at);
                """
            else:
                logger.error(f"Неподдерживаемый тип БД для создания таблицы: {db_type}")
                return False
            
            await conn.execute(text(create_sql))
            logger.info("✅ Таблица subscription_conversions успешно создана")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка создания таблицы subscription_conversions: {e}")
        return False

async def fix_subscriptions_table():
    """Исправляет структуру таблицы subscriptions, добавляя отсутствующую колонку user_id"""
    
    logger.info("=== ИСПРАВЛЕНИЕ ТАБЛИЦЫ SUBSCRIPTIONS ===")
    
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            # Проверяем существование колонки user_id
            user_id_exists = await check_column_exists('subscriptions', 'user_id')
            
            if not user_id_exists:
                logger.info("Добавляем отсутствующую колонку user_id в таблицу subscriptions")
                
                if db_type == 'sqlite':
                    column_def = 'INTEGER'
                elif db_type == 'postgresql':
                    column_def = 'INTEGER'
                elif db_type == 'mysql':
                    column_def = 'INT'
                else:
                    logger.error(f"Неподдерживаемый тип БД: {db_type}")
                    return False
                
                # Добавляем колонку user_id
                await conn.execute(text(f"ALTER TABLE subscriptions ADD COLUMN user_id {column_def}"))
                logger.info("Колонка user_id добавлена в subscriptions")
                
                # Создаем внешний ключ если это возможно
                try:
                    if db_type == 'postgresql':
                        await conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD CONSTRAINT fk_subscriptions_user_id 
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        """))
                        
                        await conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD CONSTRAINT uq_subscriptions_user_id 
                            UNIQUE (user_id)
                        """))
                        logger.info("Добавлены ограничения для user_id")
                    
                except Exception as fk_error:
                    logger.warning(f"Не удалось добавить ограничения для user_id: {fk_error}")
                
                return True
            else:
                logger.info("Колонка user_id уже существует в subscriptions")
                return True
                
    except Exception as e:
        logger.error(f"Ошибка исправления таблицы subscriptions: {e}")
        return False

async def create_cryptobot_payments_table():
    """Создает таблицу для CryptoBot платежей"""
    
    table_exists = await check_table_exists('cryptobot_payments')
    if table_exists:
        logger.info("Таблица cryptobot_payments уже существует")
        return True
    
    try:
        async with engine.begin() as conn:
            db_type = await get_database_type()
            
            if db_type == 'sqlite':
                create_sql = """
                CREATE TABLE cryptobot_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    invoice_id VARCHAR(255) UNIQUE NOT NULL,
                    amount VARCHAR(50) NOT NULL,
                    asset VARCHAR(10) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    description TEXT NULL,
                    payload TEXT NULL,
                    bot_invoice_url TEXT NULL,
                    mini_app_invoice_url TEXT NULL,
                    web_app_invoice_url TEXT NULL,
                    paid_at DATETIME NULL,
                    transaction_id INTEGER NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                );
                
                CREATE INDEX idx_cryptobot_payments_user_id ON cryptobot_payments(user_id);
                CREATE INDEX idx_cryptobot_payments_invoice_id ON cryptobot_payments(invoice_id);
                CREATE INDEX idx_cryptobot_payments_status ON cryptobot_payments(status);
                """
                
            elif db_type == 'postgresql':
                create_sql = """
                CREATE TABLE cryptobot_payments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    invoice_id VARCHAR(255) UNIQUE NOT NULL,
                    amount VARCHAR(50) NOT NULL,
                    asset VARCHAR(10) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    description TEXT NULL,
                    payload TEXT NULL,
                    bot_invoice_url TEXT NULL,
                    mini_app_invoice_url TEXT NULL,
                    web_app_invoice_url TEXT NULL,
                    paid_at TIMESTAMP NULL,
                    transaction_id INTEGER NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                );
                
                CREATE INDEX idx_cryptobot_payments_user_id ON cryptobot_payments(user_id);
                CREATE INDEX idx_cryptobot_payments_invoice_id ON cryptobot_payments(invoice_id);
                CREATE INDEX idx_cryptobot_payments_status ON cryptobot_payments(status);
                """
                
            elif db_type == 'mysql':
                create_sql = """
                CREATE TABLE cryptobot_payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    invoice_id VARCHAR(255) UNIQUE NOT NULL,
                    amount VARCHAR(50) NOT NULL,
                    asset VARCHAR(10) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    description TEXT NULL,
                    payload TEXT NULL,
                    bot_invoice_url TEXT NULL,
                    mini_app_invoice_url TEXT NULL,
                    web_app_invoice_url TEXT NULL,
                    paid_at DATETIME NULL,
                    transaction_id INT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                );
                
                CREATE INDEX idx_cryptobot_payments_user_id ON cryptobot_payments(user_id);
                CREATE INDEX idx_cryptobot_payments_invoice_id ON cryptobot_payments(invoice_id);
                CREATE INDEX idx_cryptobot_payments_status ON cryptobot_payments(status);
                """
            else:
                logger.error(f"Неподдерживаемый тип БД для создания таблицы: {db_type}")
                return False
            
            await conn.execute(text(create_sql))
            logger.info("Таблица cryptobot_payments успешно создана")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка создания таблицы cryptobot_payments: {e}")
        return False

async def fix_subscription_duplicates_universal():
    
    async with engine.begin() as conn:
        db_type = await get_database_type()
        logger.info(f"Обнаружен тип базы данных: {db_type}")
        
        try:
            result = await conn.execute(text("""
                SELECT user_id, COUNT(*) as count 
                FROM subscriptions 
                GROUP BY user_id 
                HAVING COUNT(*) > 1
            """))
            
            duplicates = result.fetchall()
            
            if not duplicates:
                logger.info("Дублирующихся подписок не найдено")
                return 0
                
            logger.info(f"Найдено {len(duplicates)} пользователей с дублирующимися подписками")
            
            total_deleted = 0
            
            for user_id_row, count in duplicates:
                user_id = user_id_row
                
                if db_type == 'sqlite':
                    delete_result = await conn.execute(text("""
                        DELETE FROM subscriptions 
                        WHERE user_id = :user_id AND id NOT IN (
                            SELECT MAX(id) 
                            FROM subscriptions 
                            WHERE user_id = :user_id
                        )
                    """), {"user_id": user_id})
                    
                elif db_type in ['postgresql', 'mysql']:
                    delete_result = await conn.execute(text("""
                        DELETE FROM subscriptions 
                        WHERE user_id = :user_id AND id NOT IN (
                            SELECT max_id FROM (
                                SELECT MAX(id) as max_id
                                FROM subscriptions 
                                WHERE user_id = :user_id
                            ) as subquery
                        )
                    """), {"user_id": user_id})
                
                else:
                    subs_result = await conn.execute(text("""
                        SELECT id FROM subscriptions 
                        WHERE user_id = :user_id 
                        ORDER BY created_at DESC, id DESC
                    """), {"user_id": user_id})
                    
                    sub_ids = [row[0] for row in subs_result.fetchall()]
                    
                    if len(sub_ids) > 1:
                        ids_to_delete = sub_ids[1:]
                        for sub_id in ids_to_delete:
                            await conn.execute(text("""
                                DELETE FROM subscriptions WHERE id = :id
                            """), {"id": sub_id})
                        delete_result = type('Result', (), {'rowcount': len(ids_to_delete)})()
                    else:
                        delete_result = type('Result', (), {'rowcount': 0})()
                
                deleted_count = delete_result.rowcount
                total_deleted += deleted_count
                logger.info(f"Удалено {deleted_count} дублирующихся подписок для пользователя {user_id}")
            
            logger.info(f"Всего удалено дублирующихся подписок: {total_deleted}")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Ошибка при очистке дублирующихся подписок: {e}")
            raise

async def run_universal_migration():
    logger.info("=== НАЧАЛО УНИВЕРСАЛЬНОЙ МИГРАЦИИ ===")
    
    try:
        db_type = await get_database_type()
        logger.info(f"Тип базы данных: {db_type}")
        
        # Исправляем таблицу subscriptions
        logger.info("=== ИСПРАВЛЕНИЕ СТРУКТУРЫ SUBSCRIPTIONS ===")
        subscriptions_fixed = await fix_subscriptions_table()
        if subscriptions_fixed:
            logger.info("✅ Структура subscriptions исправлена")
        else:
            logger.warning("⚠️ Проблемы с исправлением subscriptions")
        
        await add_remnawave_v2_columns()
        
        referral_migration_success = await add_referral_system_columns()
        if not referral_migration_success:
            logger.warning("⚠️ Проблемы с миграцией реферальной системы")
        
        logger.info("=== СОЗДАНИЕ ТАБЛИЦЫ YOOKASSA ===")
        yookassa_created = await create_yookassa_payments_table()
        if yookassa_created:
            logger.info("✅ Таблица YooKassa payments готова")
        else:
            logger.warning("⚠️ Проблемы с таблицей YooKassa payments")
        
        logger.info("=== СОЗДАНИЕ ТАБЛИЦЫ CRYPTOBOT ===")
        cryptobot_created = await create_cryptobot_payments_table()
        if cryptobot_created:
            logger.info("✅ Таблица CryptoBot payments готова")
        else:
            logger.warning("⚠️ Проблемы с таблицей CryptoBot payments")
        
        logger.info("=== СОЗДАНИЕ ТАБЛИЦЫ КОНВЕРСИЙ ПОДПИСОК ===")
        conversions_created = await create_subscription_conversions_table()
        if conversions_created:
            logger.info("✅ Таблица subscription_conversions готова")
        else:
            logger.warning("⚠️ Проблемы с таблицей subscription_conversions")
        
        async with engine.begin() as conn:
            total_subs = await conn.execute(text("SELECT COUNT(*) FROM subscriptions"))
            unique_users = await conn.execute(text("SELECT COUNT(DISTINCT user_id) FROM subscriptions WHERE user_id IS NOT NULL"))
            
            total_count = total_subs.fetchone()[0]
            unique_count = unique_users.fetchone()[0]
            
            logger.info(f"Всего подписок: {total_count}")
            logger.info(f"Уникальных пользователей: {unique_count}")
            
            if total_count == unique_count:
                logger.info("База данных уже в корректном состоянии")
                logger.info("=== МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО ===")
                return True
        
        deleted_count = await fix_subscription_duplicates_universal()
        
        async with engine.begin() as conn:
            final_check = await conn.execute(text("""
                SELECT user_id, COUNT(*) as count 
                FROM subscriptions 
                WHERE user_id IS NOT NULL
                GROUP BY user_id 
                HAVING COUNT(*) > 1
            """))
            
            remaining_duplicates = final_check.fetchall()
            
            if remaining_duplicates:
                logger.warning(f"Остались дубликаты у {len(remaining_duplicates)} пользователей")
                return False
            else:
                logger.info("=== МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО ===")
                logger.info("✅ Реферальная система обновлена")
                logger.info("✅ RemnaWave v2.1.5 колонки добавлены")
                logger.info("✅ YooKassa таблица готова")
                logger.info("✅ CryptoBot таблица готова")
                logger.info("✅ Таблица конверсий подписок создана")
                logger.info("✅ Дубликаты подписок исправлены")
                return True
                
    except Exception as e:
        logger.error(f"=== ОШИБКА ВЫПОЛНЕНИЯ МИГРАЦИИ: {e} ===")
        return False

async def check_migration_status():
    logger.info("=== ПРОВЕРКА СТАТУСА МИГРАЦИЙ ===")
    
    try:
        status = {
            "subscriptions_user_id_column": False,
            "has_made_first_topup_column": False,
            "yookassa_table": False,
            "cryptobot_table": False,
            "remnawave_v2_columns": False,
            "subscription_duplicates": False,
            "subscription_conversions_table": False
        }
        
        status["subscriptions_user_id_column"] = await check_column_exists('subscriptions', 'user_id')
        status["has_made_first_topup_column"] = await check_column_exists('users', 'has_made_first_topup')
        status["yookassa_table"] = await check_table_exists('yookassa_payments')
        status["cryptobot_table"] = await check_table_exists('cryptobot_payments')
        status["subscription_conversions_table"] = await check_table_exists('subscription_conversions')
        
        remnawave_columns = ['lifetime_used_traffic_bytes', 'last_remnawave_sync', 'trojan_password', 'vless_uuid', 'ss_password']
        remnawave_status = []
        for col in remnawave_columns:
            exists = await check_column_exists('users', col)
            remnawave_status.append(exists)
        status["remnawave_v2_columns"] = all(remnawave_status)
        
        async with engine.begin() as conn:
            duplicates_check = await conn.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT user_id, COUNT(*) as count 
                    FROM subscriptions 
                    WHERE user_id IS NOT NULL
                    GROUP BY user_id 
                    HAVING COUNT(*) > 1
                ) as dups
            """))
            duplicates_count = duplicates_check.fetchone()[0]
            status["subscription_duplicates"] = (duplicates_count == 0)
        
        check_names = {
            "subscriptions_user_id_column": "Колонка user_id в subscriptions",
            "has_made_first_topup_column": "Колонка реферальной системы",
            "yookassa_table": "Таблица YooKassa payments",
            "cryptobot_table": "Таблица CryptoBot payments",
            "subscription_conversions_table": "Таблица конверсий подписок",
            "remnawave_v2_columns": "Колонки RemnaWave v2.1.5",
            "subscription_duplicates": "Отсутствие дубликатов подписок"
        }
        
        for check_key, check_status in status.items():
            check_name = check_names.get(check_key, check_key)
            icon = "✅" if check_status else "❌"
            logger.info(f"{icon} {check_name}: {'OK' if check_status else 'ТРЕБУЕТ ВНИМАНИЯ'}")
        
        all_good = all(status.values())
        if all_good:
            logger.info("🎉 Все миграции выполнены успешно!")
        else:
            logger.warning("⚠️ Некоторые миграции требуют внимания")
            missing_migrations = [check_names[k] for k, v in status.items() if not v]
            logger.warning(f"Требуют выполнения: {', '.join(missing_migrations)}")
        
        return status
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса миграций: {e}")
        return None


