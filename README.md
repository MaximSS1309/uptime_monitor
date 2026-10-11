# Uptime Monitor

![Tests](https://github.com/MaximSS1309/uptime_monitor/actions/workflows/tests.yml/badge.svg)

Асинхронний сервіс моніторингу доступності сайтів на FastAPI. Користувачі
реєструються, додають свої сайти, а фонова задача періодично перевіряє їх і
зберігає історію перевірок у PostgreSQL. Керування відбувається через REST API
з JWT-автентифікацією.

## Можливості

- Реєстрація та вхід користувачів, JWT-токени, паролі зберігаються як argon2-хеш
- CRUD для сайтів: кожен користувач бачить і змінює лише **свої** сайти
- Фонова задача перевіряє всі сайти паралельно кожні 10 секунд (таймаут запиту 10 с)
- Історія кожної перевірки (статус-код, час, онлайн/офлайн)
- Пагінація для списків сайтів і логів
- Міграції бази даних через Alembic
- Автотести (pytest) і CI на GitHub Actions
- Автогенерована документація API (Swagger / ReDoc)

## Стек технологій

| Категорія        | Технологія                                   |
|------------------|-----------------------------------------------|
| Backend          | FastAPI, Python 3.13                          |
| ORM              | SQLAlchemy 2.0 (async)                        |
| База даних       | PostgreSQL 16 (драйвер asyncpg)               |
| Міграції         | Alembic                                       |
| Автентифікація   | PyJWT, pwdlib (argon2)                        |
| HTTP-клієнт      | httpx (async, для перевірки сайтів)           |
| Валідація        | Pydantic v2                                   |
| Тести            | pytest, pytest-asyncio, SQLite in-memory      |
| CI               | GitHub Actions                                |
| Контейнеризація  | Docker, Docker Compose                        |

## Швидкий старт (Docker)

```bash
git clone https://github.com/MaximSS1309/uptime_monitor.git
cd uptime_monitor
docker compose up -d --build
```

Контейнер `app` сам застосує міграції (`alembic upgrade head`) перед стартом
сервера. Після запуску:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

За замовчуванням `docker-compose.yml` використовує тестовий `SECRET_KEY`.
Для реального використання створіть файл `.env` (див. нижче) і задайте власний
ключ, Compose підхопить його автоматично.

## Локальний запуск (Postgres у Docker, застосунок локально)

```bash
# 1. Підняти лише базу даних
docker compose up -d postgres

# 2. Віртуальне середовище та залежності
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Налаштування середовища
cp .env.example .env             # Windows: copy .env.example .env
# згенеруйте секретний ключ і впишіть його в .env як SECRET_KEY:
python -c "import secrets; print(secrets.token_hex(32))"

# 4. Міграції та запуск
alembic upgrade head
uvicorn app.main:app --reload
```

## Змінні середовища

| Змінна                        | Опис                                         | Приклад                                                        |
|-------------------------------|----------------------------------------------|-----------------------------------------------------------------|
| `DATABASE_URL`                | Рядок підключення до PostgreSQL (async)      | `postgresql+asyncpg://user:pass@localhost:5433/site_monitor`   |
| `SECRET_KEY`                  | Ключ підпису JWT, обов'язковий               | випадковий рядок від 32 байт                                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Час життя токена в хвилинах (за замовч. 30)  | `30`                                                            |
| `DEBUG`                       | Виводити SQL-запити в консоль (`true/false`) | `false`                                                         |

Без `SECRET_KEY` застосунок свідомо не запускається.

## API

Повна інтерактивна документація: `/docs`. У Swagger кнопка **Authorize** дозволяє
увійти (у полі `username` вводиться email) і викликати захищені ендпоінти.

| Метод  | Шлях                | Доступ    | Опис                                 |
|--------|---------------------|-----------|--------------------------------------|
| POST   | `/auth/register`    | відкритий | Реєстрація користувача               |
| POST   | `/auth/login`       | відкритий | Вхід, повертає JWT (OAuth2 password) |
| GET    | `/auth/me`          | токен     | Поточний користувач                  |
| POST   | `/sites/`           | токен     | Додати сайт для моніторингу          |
| GET    | `/sites/`           | токен     | Список власних сайтів (пагінація)    |
| GET    | `/sites/{id}`       | токен     | Один сайт                            |
| PUT    | `/sites/{id}`       | токен     | Оновити сайт (часткове оновлення)    |
| DELETE | `/sites/{id}`       | токен     | Видалити сайт разом з логами         |
| GET    | `/sites/{id}/logs`  | токен     | Історія перевірок (пагінація)        |

Пагінація: параметри `skip` (за замовч. 0) і `limit` (за замовч. 50, максимум 200).

### Приклад

```bash
# 1. Реєстрація
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "me@example.com", "password": "supersecret123"}'

# 2. Вхід (форма, поле username = email)
curl -X POST http://localhost:8000/auth/login \
  -d "username=me@example.com&password=supersecret123"
# -> {"access_token": "<TOKEN>", "token_type": "bearer"}

# 3. Додати сайт
curl -X POST http://localhost:8000/sites/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Example", "url": "https://example.com"}'
```

## Міграції (Alembic)

Схема БД керується міграціями, а не автоматичним `create_all`.

```bash
alembic upgrade head                              # застосувати всі міграції
alembic revision --autogenerate -m "опис зміни"   # нова міграція після зміни моделей
alembic downgrade -1                              # відкотити останню
```

У Docker міграції застосовуються автоматично при старті контейнера `app`.

## Тести

```bash
pip install -r requirements-dev.txt
pytest -v
```

Тести працюють на ізольованій SQLite in-memory базі, тому Docker і Postgres для
них не потрібні. Покрито: CRUD сайтів, пагінацію, коди помилок (401, 404, 409, 422),
реєстрацію та вхід, прострочені й підроблені токени, а також ізоляцію даних між
користувачами. Ті самі тести автоматично запускаються в GitHub Actions при кожному
пуші.

## Структура проєкту

```
.
├── app/
│   ├── main.py          # застосунок FastAPI, lifespan, підключення роутерів
│   ├── auth.py          # хешування паролів, JWT, залежність get_current_user
│   ├── auth_router.py   # /auth/register, /auth/login, /auth/me
│   ├── routers.py       # CRUD для /sites
│   ├── models.py        # SQLAlchemy-моделі: User, Site, CheckLog
│   ├── schemas.py       # Pydantic-схеми запитів і відповідей
│   ├── services.py      # фонова задача моніторингу
│   └── database.py      # engine, сесії, get_db
├── alembic/             # міграції
├── tests/               # pytest
├── .github/workflows/   # CI
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── requirements-dev.txt
```

## Архітектурні рішення

- **Чужий ресурс повертає 404, а не 403**, щоб не розкривати, що сайт з таким id існує.
- **Унікальність URL діє в межах одного користувача**: різні люди можуть моніторити
  той самий сайт, але не додавати його двічі собі.
- **Хешування паролів (argon2) виконується в окремому потоці**, щоб не блокувати
  event loop. Вхід з неіснуючим email і з неправильним паролем неможливо відрізнити
  ні за відповіддю, ні за часом.
- **Перевірки сайтів виконуються паралельно** через `asyncio.gather` із таймаутом,
  тож один завислий сайт не затримує решту.
- **Каскадне видалення**: разом із сайтом видаляються його логи (на рівні БД).

## Відомі обмеження та плани

- Сайт вважається онлайн лише при статусі 200 (після redirect-ів).
- Інтервал перевірки глобальний (10 с), без налаштування на рівні сайту.
- Монітор працює в одному процесі з API: при кількох воркерах кожен перевірятиме
  всі сайти. Варто винести в окремий сервіс або додати розподіл задач.
- Таблиця `check_logs` росте без обмежень: потрібна політика очищення старих записів.
- Немає refresh-токенів і rate limiting на вхід.
- [ ] Сповіщення (email/Telegram) при падінні сайту
- [ ] Інтервал і критерій «онлайн» для кожного сайту окремо

## Ліцензія

MIT
