# 🚀 Remnawave Bedolaga Bot

<div align="center">

![Logo](./assets/logo2.svg)

**🤖 Современный Telegram-бот для управления VPN подписками через Remnawave API**

*Полнофункциональное решение с управлением пользователями, платежами и администрированием*

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Fr1ngg/remnawave-bedolaga-telegram-bot?style=social)](https://github.com/Fr1ngg/remnawave-bedolaga-telegram-bot/stargazers)

[🚀 Быстрый старт](#-быстрый-старт) • [📖 Функционал](#-функционал) • [🐳 Docker](#-docker-развертывание) • [💬 Поддержка](#-поддержка)

</div>

---

## 🧪 ([Тестирование бота](https://t.me/FringVPN_bot))

## 💬 **[Bedolaga Chat](https://t.me/+wTdMtSWq8YdmZmVi)** - Для общения, вопросов, предложений

## 🌟 Почему Bedolagа?
Бот Бедолага не добрый и не милый.
Он просто делает вашу работу вместо вас, принимает оплату, выдаёт подписки, интегрируется с Remnawave и тихо ненавидит всех, кто ещё не подключил его.

Вы хотите продавать VPN — Бедолага позволит это делать.
Вы хотите спать — он позволит и это.

### ⚡ **Полная автоматизация VPN бизнеса**
- 🎯 **Готовое решение** - разверни за 5 минут, начни продавать сегодня
- 💰 **Многоканальные платежи** - Telegram Stars + Tribute + ЮKassa
- 🔄 **Автоматизация 99%** - от регистрации до продления подписок
- 📊 **Детальная аналитика**
  
### 🎛️ **Гибкость конфигурации**
- 🌍 **Выбор стран** - пользователи сами выбирают нужные локации
- 📱 **Управление устройствами** - от 1 до 10 шт (С настройкой кол-ва бесплатных у триальных и платных подписок)
- 📊 **Гибкие тарифы** - от 5GB до безлимита, от 14 дней до года
- 🎁 **Промо-система** - коды на деньги, дни подписки, триал-периоды
- 3 режима показа ссылки подписки: 1) С гайдом по подключению прямо в боте(тянущий данные приложений и ссылок на скачку из app-config.json) 2) Обычное открытие ссылки подписки в миниапе 3) Интеграция сабпейджа maposia - кастомно прописать ссылку можно
- Возможность переключаться между пакетной продажей трафика и фиксированной(Пропуская шаг выбора пакета трафика при оформлении/настройки подписки юзера)
- Возможность задать доступные дни для покупки первой подписки и при продлении

### 💪 **Enterprise готовность**
- 🏗️ **Современная архитектура** - AsyncIO, PostgreSQL, Redis
- 🔒 **Безопасность** - шифрование, валидация, rate limiting
- 📈 **Масштабируемость** 
- 🔧 **Мониторинг** - Prometheus, Grafana, health checks
- 🔧 **Режим технических работ** - Ручное включение + Мониторинг системы, который в случае падении панели Remnawave переведет бота в режим технических работ и обратно - отключит его, если панель поднимется.
- Интеграция с системой защиты панели Remnawave через куки-аутентификацию, которая используется в [remnawave-reverse-proxy](https://github.com/eGamesAPI/remnawave-reverse-proxy) для скрытия панели от несанкционированного доступа.

---

## 🚀 Быстрый старт

### 🐳 Docker запуск

```bash
# 1. Скачай репозиторий
git clone https://github.com/Fr1ngg/remnawave-bedolaga-telegram-bot.git
cd remnawave-bedolaga-telegram-bot

# 2. Настрой конфиг
cp .env.example .env
nano .env  # Заполни токены и настройки

# 3. Создай необходимые директории
mkdir -p logs data

# 4. Запусти всё разом
docker compose up -d

# 5. Проверь статус
docker compose logs 
```

### ⚙️ ENV параметры

| Настройка | Где взять | Пример |
|-----------|-----------|---------|
| 🤖 **BOT_TOKEN** | [@BotFather](https://t.me/BotFather) | `1234567890:AABBCCdd...` |
| 🔑 **REMNAWAVE_API_KEY** | Твоя Remnawave панель | `eyJhbGciOiJIUzI1...` |
| 🌐 **REMNAWAVE_API_URL** | URL твоей панели | `https://panel.example.com` |
| 👑 **ADMIN_IDS** | Твой Telegram ID | `123456789,987654321` |

<details>
<summary> 🔧 ВСЕ ПАРАМЕТРЫ .env</summary>

```env
# ===============================================
# 🤖 REMNAWAVE BEDOLAGA BOT CONFIGURATION
# ===============================================

# ===== TELEGRAM BOT =====
BOT_TOKEN=
ADMIN_IDS=
SUPPORT_USERNAME=@support

# ===== DATABASE =====
# Для Docker используйте PostgreSQL:
DATABASE_URL=postgresql+asyncpg://remnawave_user:secure_password_123@postgres:5432/remnawave_bot
# Для локального запуска без Docker используйте SQLite: sqlite+aiosqlite:///./bot.db 
# DATABASE_URL=postgresql+asyncpg://remnawave_user:secure_password_123@postgres:5432/remnawave_bot

REDIS_URL=redis://redis:6379/0

# Пароли для Docker (PostgreSQL/Redis)
POSTGRES_DB=remnawave_bot
POSTGRES_USER=remnawave_user
POSTGRES_PASSWORD=secure_password_123

# ===== REMNAWAVE API =====
REMNAWAVE_API_URL=https://panel.example.com
REMNAWAVE_API_KEY=
# Для панелей установленных скриптом eGames прописывать ключ в формате XXXXXXX:DDDDDDDD - https://panel.example.com/auth/login?XXXXXXX=DDDDDDDD
REMNAWAVE_SECRET_KEY=your_secret_key_here

# ========= ПОДПИСКИ =========
# ===== ТРИАЛ ПОДПИСКА =====
TRIAL_DURATION_DAYS=3
TRIAL_TRAFFIC_LIMIT_GB=10
TRIAL_DEVICE_LIMIT=1
TRIAL_SQUAD_UUID=

# ===== ПЛАТНАЯ ПОДПИСКА =====
# Сколько устройств доступно по дефолту при покупке платной подписки
DEFAULT_DEVICE_LIMIT=3

# Максимум устройств достопных к покупке (0 = Нет лимита)
MAX_DEVICES_LIMIT=15

# Дефолт параметры для подписок выданных через админку
DEFAULT_TRAFFIC_LIMIT_GB=100

# ===== ГЛОБАЛЬНЫЙ ПАРАМЕТР ДЛЯ ВСЕХ ПОДПИСОК =====
DEFAULT_TRAFFIC_RESET_STRATEGY=MONTH

# ===== НАСТРОЙКИ ТРАФИКА =====
# Режим выбора трафика:
# "selectable" - пользователи выбирают пакеты трафика (по умолчанию)
# "fixed" - фиксированный лимит трафика для всех подписок
TRAFFIC_SELECTION_MODE=selectable

# Фиксированный лимит трафика в ГБ (используется только в режиме "fixed")
# 0 = безлимит
FIXED_TRAFFIC_LIMIT_GB=100

# ===== ПЕРИОДЫ ПОДПИСКИ =====
# Доступные периоды подписки (через запятую)
# Возможные значения: 14,30,60,90,180,360
AVAILABLE_SUBSCRIPTION_PERIODS=30,90,180
AVAILABLE_RENEWAL_PERIODS=30,90,180

# ===== ЦЕНЫ (в копейках) =====
BASE_SUBSCRIPTION_PRICE=0

# Цены за периоды
PRICE_14_DAYS=7000
PRICE_30_DAYS=9900
PRICE_60_DAYS=25900
PRICE_90_DAYS=36900
PRICE_180_DAYS=69900
PRICE_360_DAYS=109900

# Выводимые пакеты трафика и их цены в копейках
TRAFFIC_PACKAGES_CONFIG="5:2000:false,10:3500:false,25:7000:false,50:11000:true,100:15000:true,250:17000:false,500:19000:false,1000:19500:true,0:20000:true"

# Цена за дополнительное устройство (DEFAULT_DEVICE_LIMIT идет бесплатно!)
PRICE_PER_DEVICE=5000

# ===== РЕФЕРАЛЬНАЯ СИСТЕМА =====
REFERRAL_REGISTRATION_REWARD=10000
REFERRED_USER_REWARD=10000
REFERRAL_COMMISSION_PERCENT=25

# ===== АВТОПРОДЛЕНИЕ =====
AUTOPAY_WARNING_DAYS=3,1
DEFAULT_AUTOPAY_DAYS_BEFORE=3
MIN_BALANCE_FOR_AUTOPAY_KOPEKS=10000

# ===== ПЛАТЕЖНЫЕ СИСТЕМЫ =====

# Telegram Stars (работает автоматически)
TELEGRAM_STARS_ENABLED=true
TELEGRAM_STARS_RATE_RUB=1.3

# Tribute (https://tribute.app)
TRIBUTE_ENABLED=false
TRIBUTE_API_KEY=
TRIBUTE_WEBHOOK_SECRET=your_webhook_secret
TRIBUTE_DONATE_LINK=
TRIBUTE_WEBHOOK_PATH=/tribute-webhook
TRIBUTE_WEBHOOK_PORT=8081

# YooKassa (https://yookassa.ru)
YOOKASSA_ENABLED=false
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
YOOKASSA_RETURN_URL=
YOOKASSA_DEFAULT_RECEIPT_EMAIL=receipts@yourdomain.com

# Настройки чеков для налоговой
YOOKASSA_VAT_CODE=1
# Коды НДС:
# 1 - НДС не облагается
# 2 - НДС 0%
# 3 - НДС 10%
# 4 - НДС 20%
# 5 - НДС 10/110
# 6 - НДС 20/120

YOOKASSA_PAYMENT_MODE=full_payment
# Способы расчета:
# full_payment - полная оплата
# partial_payment - частичная оплата
# advance - аванс
# full_prepayment - полная предоплата
# partial_prepayment - частичная предоплата
# credit - передача в кредит
# credit_payment - оплата кредита

YOOKASSA_PAYMENT_SUBJECT=service
# Предметы расчета:
# commodity - товар
# excise - подакцизный товар
# job - работа
# service - услуга
# gambling_bet - ставка в азартной игре
# gambling_prize - выигрыш в азартной игре
# lottery - лотерейный билет
# lottery_prize - выигрыш в лотерее
# intellectual_activity - результат интеллектуальной деятельности
# payment - платеж
# agent_commission - агентское вознаграждение
# composite - составной предмет расчета
# another - другое

# Webhook настройки
YOOKASSA_WEBHOOK_PATH=/yookassa-webhook
YOOKASSA_WEBHOOK_PORT=8082
YOOKASSA_WEBHOOK_SECRET=your_webhook_secret

# ===== НАСТРОЙКИ ОПИСАНИЙ ПЛАТЕЖЕЙ =====
# Эти настройки позволяют изменить описания платежей, 
# чтобы избежать блокировок платежных систем
PAYMENT_SERVICE_NAME=Интернет-сервис
PAYMENT_BALANCE_DESCRIPTION=Пополнение баланса
PAYMENT_SUBSCRIPTION_DESCRIPTION=Оплата подписки
PAYMENT_BALANCE_TEMPLATE={service_name} - {description}
PAYMENT_SUBSCRIPTION_TEMPLATE={service_name} - {description}

# ===== ИНТЕРФЕЙС И UX =====

# Режим работы кнопки "Подключиться"
# guide - открывает гайд подключения (режим 1)
# miniapp_subscription - открывает ссылку подписки в мини-приложении (режим 2)
# miniapp_custom - открывает заданную ссылку в мини-приложении (режим 3)
CONNECT_BUTTON_MODE=guide

# URL для режима miniapp_custom (обязателен при CONNECT_BUTTON_MODE=miniapp_custom)
MINIAPP_CUSTOM_URL=

# ===== МОНИТОРИНГ И УВЕДОМЛЕНИЯ =====
MONITORING_INTERVAL=60
INACTIVE_USER_DELETE_MONTHS=3

# Уведомления
TRIAL_WARNING_HOURS=2
ENABLE_NOTIFICATIONS=true
NOTIFICATION_RETRY_ATTEMPTS=3
MONITORING_LOGS_RETENTION_DAYS=30
NOTIFICATION_CACHE_HOURS=24

# ===== РЕЖИМ ТЕХНИЧЕСКИХ РАБОТ =====
MAINTENANCE_MODE=false
MAINTENANCE_CHECK_INTERVAL=30
MAINTENANCE_AUTO_ENABLE=true
MAINTENANCE_MESSAGE=Ведутся технические работы. Сервис временно недоступен. Попробуйте позже.

# ===== ЛОКАЛИЗАЦИЯ =====
DEFAULT_LANGUAGE=ru
AVAILABLE_LANGUAGES=ru,en

# ===== ЛОГИРОВАНИЕ =====
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# ===== РАЗРАБОТКА =====
DEBUG=false
WEBHOOK_URL=
WEBHOOK_PATH=/webhook

# ===== ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ =====
# Конфигурация приложений для гайда подключения
APP_CONFIG_PATH=app-config.json
ENABLE_DEEP_LINKS=true
APP_CONFIG_CACHE_TTL=3600
```

</details>

---

## 🐳 Docker развертывание

### 📄 docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: remnawave_bot_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-remnawave_bot}
      POSTGRES_USER: ${POSTGRES_USER:-remnawave_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secure_password_123}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - bot_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-remnawave_user} -d ${POSTGRES_DB:-remnawave_bot}"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    container_name: remnawave_bot_redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - bot_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  bot:
    image: fr1ngg/remnawave-bedolaga-telegram-bot:latest
    container_name: remnawave_bot
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-remnawave_user}:${POSTGRES_PASSWORD:-secure_password_123}@postgres:5432/${POSTGRES_DB:-remnawave_bot}
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./logs:/app/logs:rw
      - ./data:/app/data:rw
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "${TRIBUTE_WEBHOOK_PORT:-8081}:8081"
      - "${YOOKASSA_WEBHOOK_PORT:-8082}:8082"
    networks:
      - bot_network
    user: "1000:1000"
    command: >
      bash -c "
        mkdir -p /app/logs /app/data &&
        python main.py
      "

volumes:
  postgres_data:
  redis_data:

networks:
  bot_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 🔧 Настройка webhook'ов (для Tribute/YooKassa)

#### Через Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /tribute-webhook {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /yookassa-webhook {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8081/health;
    }
}
```

#### Через Caddy

```caddyfile
your-domain.com {
    handle /tribute-webhook* {
        reverse_proxy localhost:8081
    }
    
    handle /yookassa-webhook* {
        reverse_proxy localhost:8082
    }
    
    handle /health {
        reverse_proxy localhost:8081/health
    }
}
```

### 🚀 Команды управления

```bash
# Быстрый старт
docker compose up -d

# Статус сервисов
docker compose ps

# Логи
docker compose logs

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Полная очистка
docker compose down -v --remove-orphans
```

---

## ⭐ Функционал

<table>
<tr>
<td width="50%" valign="top">

### 👤 **Для пользователей**

🛒 **Умная покупка подписок**
- 📅 Выбор периода (14-360 дней) (С возможностью настройки выводимых периодов 14/30/60/90/180/360 дней)
- 📊 Настройка трафика (5GB - безлимит) (Можно откоючить данный шаг, всем подпискам выдавать единый)
- 🌍 Выбор стран через сквады (Доступно при наличие двух стран(сквадов) в продаже)
- 📱 Количество устройств (1-5)

 🧪 **Тестовая подписка**
 - Получение настраиваемой разовой тестовой подписки
 - Уведомления об истечении с предложением о переходе н платную версию

💰 **Удобные платежи**
- ⭐ Telegram Stars 
- 💳 Tribute 
- 💳 YooKassa
- 🎁 Реферальные бонусы
- Детальная история транзакций 

📱 **Управление подписками**
- 📈 Просмотр статистики использования
- 🔄 Автопродление с баланса
- 🔄 Сброс/увеличение трафика
- 🌍 Смена стран на лету (Доступно при наличие двух стран(сквадов) в продаже)
- 📱 Настройка устройств с возможностью докупки(до 10ти устройств) + сброса устройств

🎁 **Бонусная система**
- 🎫 Промокоды на деньги/дни
- 👥 Реферальная программа 
- 🔔 Ежедневные уведомления

</td>
<td width="50%" valign="top">

### ⚙️ **Для администраторов**

📊 **Мощная аналитика**
- 👥 Детальная статистика пользователей
- 💰 Анализ подписок и платежей
- 🖥️ Мониторинг серверов Remnawave
- 📈 Финансовые отчеты

👥 **Управление пользователями**
- 🔍 Поиск и редактирование профилей
- 💰 Управление балансами
- 🚫 Блокировка/разблокировка/удаление

🎫 **Промо-система**
- 🎁 Создание промокодов (деньги/дни/длинный триал)
- 📊 Статистика использования
- ⚙️ Полное редактирование промокодов (Изминение условий, активация/деактивация/удаление + статистика применения) 

🖥️ **Мониторинг системы**
- 💚 Состояние Remnawave панели
- 🔄 Синхронизация данных (Передача данных из панели в бота)
- 🌐 Управление сквадами 
- 📋 Логи и диагностика
- 🚧 Автоматический режим тех. работ (Включение в случае падения коннекта с панелью Remnawave c уведомлениями администраторам)

📨 **Коммуникации**
- 📢 Рассылки по сегментам
- 🔔 Автоуведомления о продлении
- 💬 Система поддержки
- 📝 Настройка правил сервиса
- Поддержка HTML разметки 

🚧 **Режим технических работ**
- Ручное включение/отключение с указанием причины
- Включение/выключение мониторинга состояния панели (проверяет соеденение до панели раз в 30 сек(можно изменить промежуток)
- Принудительаная проверка API

📖 **Правила сервиса**
- Настройка правил сервиса
- Просмотр текущих правил

</td>
</tr>
</table>

---

## 🔧 Первичная настройка в боте

После запуска необходимо:

1. **📡 Синхронизация серверов** (обязательно!)
   - Зайди в бот → **Админ панель** → **Подписки** → **Управление серверами**
   - Нажми **Синхронизация** и дождись завершения
   - Без этого пользователи не смогут выбирать страны!

2. **👥 Синхронизация пользователей** (если есть база)
   - **Админ панель** → **Remnawave** → **Синхронизация**
   - **Синхронизировать всех** → дождись импорта

### 💳 Настройка платежных систем

#### Telegram Stars
Работает автоматически после указания `BOT_TOKEN`.

#### Tribute
1. Зарегистрируйся на https://tribute.app
2. Создай донат-ссылку
3. Получи API ключ
4. Настрой webhook в Tribute: `https://your-domain.com/tribute-webhook`

#### YooKassa
1. Зарегистрируйся в ЮKassa
2. Получи Shop ID и Secret Key
3. Настрой webhook в YooKassa: `https://your-domain.com/yookassa-webhook`

---

## 💡 Использование

### 👤 **Для пользователей**

1. **🚀 Старт** → Найди бота и нажми `/start`
2. **📋 Правила** → Прими правила сервиса 
3. **💰 Баланс** → "💰 Баланс" → пополни через Stars/Tribute
4. **🛒 Подписка** → "🛒 Купить подписку" → выбор тарифа → оплата
5. **📱 Управление** → "📋 Мои подписки" → конфигурация → получение ссылки
6. **👥 Рефералы** → "👥 Рефералы" → поделись ссылкой

### ⚙️ **Для администраторов**

Доступ через **"⚙️ Админ панель"**:

- **📦 Подписки** → настройка серверов, цен, синхронизация
- **👥 Пользователи** → поиск, редактирование, блокировка
- **🎁 Промокоды** → создание бонусов, статистика
- **📨 Рассылки** → уведомления по сегментам
- **🖥 Remnawave** → мониторинг панели, синхронизация
- **📊 Статистика** → детальная аналитика бизнеса

---

## 🚀 Производительность

| Пользователей | Память | CPU | Диск | Описание |
|---------------|--------|-----|------|----------|
| **1,000** | 512MB | 1 vCPU | 10GB | ✅ Стартап |
| **10,000** | 2GB | 2 vCPU | 50GB | ✅ Малый бизнес |
| **50,000** | 4GB | 4 vCPU | 100GB | ✅ Средний бизнес |
| **100,000+** | 8GB+ | 8+ vCPU | 200GB+ | 🚀 Enterprise |

---

## 🐛 Устранение неполадок

### Health Checks
- Основной: `http://localhost:8081/health`
- YooKassa: `http://localhost:8082/health`

### Полезные команды
```bash
# Просмотр логов
docker compose logs -f bot

# Статус контейнеров
docker compose ps

# Перезапуск бота
docker compose restart bot

# Проверка базы данных
docker compose exec postgres pg_isready -U remnawave_user
```

### Частые проблемы

| Проблема | Решение |
|----------|---------|
| Бот не отвечает | Проверь `BOT_TOKEN` и интернет |
| Ошибки БД | Проверь статус PostgreSQL контейнера |
| Webhook не работает | Проверь настройки прокси-сервера |
| API Remnawave недоступен | Проверь `REMNAWAVE_API_URL` и ключ |

---

## 🏗️ Архитектура

### 💪 Современный стек технологий

- **🐍 Python 3.11+** с AsyncIO - максимальная производительность
- **🗄️ PostgreSQL 15+** - надежное хранение данных
- **⚡ Redis** - быстрое кеширование и сессии
- **🐳 Docker** - простое развертывание в любой среде
- **🔗 SQLAlchemy ORM** - безопасная работа с БД
- **🚀 aiogram 3** - современная Telegram Bot API

### 📁 Структура проекта

```
bedolaga_bot/
├── 🎯 main.py                     # Точка входа
├── 📦 requirements.txt            # Зависимости
├── ⚙️ .env.example               # Конфиг
├── ⚙️ app-config.json            # Информация для гайда в боте по подключению
│
├── 📱 app/
│   ├── 🤖 bot.py                 # Инициализация бота
│   ├── ⚙️ config.py              # Настройки
│   ├── 🎛️ states.py              # FSM состояния
│   │
│   ├── 🎮 handlers/              # Обработчики событий
│   │   ├── 🏠 start.py           # Регистрация и старт
│   │   ├── 🛒 subscription.py    # Подписки
│   │   ├── 💰 balance.py         # Баланс и платежи
│   │   ├── 🎁 promocode.py       # Промокоды
│   │   ├── 👥 referral.py        # Реферальная система
│   │   ├── 💬 support.py         # Техподдержка
│   │   └── 👑 admin/             # Админ панель
│   │       ├── 📊 statistics.py  # Статистика
│   │       ├── 👥 users.py       # Управление юзерами
│   │       ├── 🎫 promocodes.py  # Управление промокодами
│   │       ├── 📨 messages.py    # Рассылки
│   │       ├── 🔍 monitoring.py  # Мониторинг
│   │       └── 🔗 remnawave.py   # Система RemnaWave
│   │
│   ├── 🗄️ database/             # База данных
│   │   ├── 📊 models.py          # Модели SQLAlchemy
│   │   ├── 🔗 database.py        # Подключение к БД
│   │   └── 📝 crud/              # CRUD операции
│   │
│   ├── 🔧 services/             # Бизнес-логика
│   │   ├── 👤 user_service.py             # Сервис пользователей
│   │   ├── 📋 subscription_service.py     # Сервис подписок
│   │   ├── 💰 payment_service.py          # Платежи
│   │   ├── 🎁 promocode_service.py        # Промокоды
│   │   ├── 👥 referral_service.py         # Рефералы
│   │   ├── 🔍 monitoring_service.py       # Мониторинг
│   │   └── 🌐 remnawave_service.py       # Интеграция с Remnawave
│   │
│   ├── 🛠️ utils/                # Утилиты
│   ├── 🛡️ middlewares/           # Middleware
│   ├── 🌐 localization/          # Локализация
│   └── 🔌 external/              # Внешние API
│
├── 🔄 migrations/                # Миграции БД
└── 📋 logs/                      # Логи системы
```

---

## 🤝 Как помочь проекту

- 🔍 [Сообщай о багах](https://github.com/Fr1ngg/remnawave-bedolaga-telegram-bot/issues) с подробным описанием
- 💡 [Предлагай идеи](https://github.com/Fr1ngg/remnawave-bedolaga-telegram-bot/discussions) для улучшения
- ⭐ **Ставь звезды** проекту - это мотивирует!
- 📢 **Рассказывай друзьям** о проекте
- 💝 **[Поддержи разработку](https://t.me/tribute/app?startapp=duUO)** - помоги проекту расти

---

## 💬 Поддержка и сообщество

### 📞 **Контакты**

- **💬 Telegram:** [@fringg](https://t.me/fringg) - вопросы по разработке (только по делу!)
- **💬 Telegram Group:** [Bedolaga Chat](https://t.me/+wTdMtSWq8YdmZmVi) - Для общения, вопросов, предложений, багов
- **🐛 Issues:** [GitHub Issues](https://github.com/Fr1ngg/remnawave-bedolaga-telegram-bot/issues) - баги и предложения

### 📚 **Полезные ресурсы**

- **📖 [Remnawave Docs](https://docs.remna.st)** - документация панели
- **🤖 [Telegram Bot API](https://core.telegram.org/bots/api)** - API ботов
- **🐳 [Docker Guide](https://docs.docker.com/get-started/)** - обучение Docker

---

## 💝 Благодарности

### 🌟 **Топ спонсоры проекта**

<table align="center">
<tr>
<th>🥇 Место</th>
<th>👤 Спонсор</th>
<th>💰 Сумма</th>
<th>💬 От себя благодарю</th>
</tr>
<tr>
<td>🥇</td>
<td><strong>Илья (@ispanec_nn)</strong></td>
<td>$30</td>
<td>За веру в проект с самого начала</td>
</tr>
<tr>
<td>🥈</td>
<td><strong>@pilot_737800</strong></td>
<td>₽2,250</td>
<td>За активное тестирование и фидбек</td>
</tr>
<tr>
<td>🥉</td>
<td><strong>@Legacyyy777</strong></td>
<td>₽1,000</td>
<td>За ценные предложения по улучшению</td>
</tr>
</table>

### 🌟 **Особая благодарность**

- **Remnawave Team** - за отличную панель и API

---

<div align="center">

## 📄 Лицензия

Проект распространяется под лицензией **MIT**

---
