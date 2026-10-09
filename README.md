# Uptime Monitor

Асинхронний сервіс моніторингу доступності сайтів на FastAPI. Періодично перевіряє
список сайтів, зберігає історію перевірок у PostgreSQL і надає REST API для управління
списком сайтів та перегляду логів.

## Можливості

- Додавання, редагування, видалення сайтів для моніторингу (`CRUD`)
- Фонова задача перевіряє всі сайти паралельно кожні 10 секунд
- Історія кожної перевірки (статус-код, час, онлайн/офлайн) зберігається в БД
- Пагінація для списків сайтів та логів
- Автогенерована документація API (Swagger / ReDoc)

## Стек технологій

| Категорія      | Технологія                          |
|----------------|--------------------------------------|
| Backend        | FastAPI, Python 3.13                 |
| ORM            | SQLAlchemy 2.0 (async)               |
| База даних     | PostgreSQL                           |
| HTTP-клієнт    | httpx (async, для перевірки сайтів)  |
| Валідація      | Pydantic v2                          |
| Контейнеризація| Docker, Docker Compose               |

## Швидкий старт (Docker)

Найпростіший спосіб — підняти все одразу через Docker Compose:

```bash
git clone https://github.com/<your-username>/uptime-monitor.git
cd uptime-monitor
docker compose up -d --build
```

Застосунок буде доступний на `http://localhost:8000`, документація API — на
`http://localhost:8000/docs`.

## Локальний запуск (без Docker для застосунку)

Якщо хочете піднімати сам застосунок локально (наприклад, для дебагу), а Postgres
тримати в Docker:

```bash
# 1. Підняти тільки базу даних
docker compose up -d postgres

# 2. Встановити залежності
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Створити .env (див. .env.example)
cp .env.example .env

# 4. Запустити застосунок
uvicorn app.main:app --reload
```

## Змінні середовища

| Змінна         | Опис                                      | Приклад                                                              |
|----------------|--------------------------------------------|-----------------------------------------------------------------------|
| `DATABASE_URL` | Рядок підключення до PostgreSQL (async)    | `postgresql+asyncpg://user:pass@localhost:5433/site_monitor`         |
| `DEBUG`        | Вивід SQL-запитів у консоль (`true/false`) | `false`                                                                |

## API

Повна інтерактивна документація доступна на `/docs` (Swagger) або `/redoc`.

| Метод  | Шлях                    | Опис                                  |
|--------|--------------------------|----------------------------------------|
| POST   | `/sites/`                | Додати новий сайт для моніторингу      |
| GET    | `/sites/`                | Список сайтів (з пагінацією)           |
| GET    | `/sites/{id}`            | Отримати один сайт                     |
| PUT    | `/sites/{id}`            | Оновити сайт                           |
| DELETE | `/sites/{id}`            | Видалити сайт                          |
| GET    | `/sites/{id}/logs`       | Історія перевірок сайту (з пагінацією) |

### Приклад запиту

```bash
curl -X POST http://localhost:8000/sites/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Example", "url": "https://example.com"}'
```

## Структура проєкту

```
app/
├── main.py         # Точка входу, налаштування FastAPI, lifespan
├── routers.py       # REST-ендпоінти
├── models.py         # SQLAlchemy-моделі
├── schemas.py        # Pydantic-схеми (вхід/вихід)
├── services.py        # Фонова задача моніторингу сайтів
└── database.py         # Підключення до БД, сесії
```

## Міграції бази даних (Alembic)

Схема БД керується через Alembic-міграції, а не автоматичним `create_all`.

```bash
# Застосувати всі міграції (створити/оновити таблиці)
alembic upgrade head

# Створити нову міграцію після зміни моделей у app/models.py
alembic revision --autogenerate -m "опис зміни"

# Відкотити останню міграцію
alembic downgrade -1
```

При запуску через `docker compose up`, контейнер `app` сам виконує
`alembic upgrade head` перед стартом сервера — вручну нічого запускати не треба.

Якщо запускаєте застосунок локально (не в Docker), виконайте `alembic upgrade head`
один раз перед першим стартом `uvicorn`.

## Що можна покращити далі

- [ ] Автентифікація користувачів (JWT), прив'язка сайтів до власника
- [ ] Сповіщення (email/Telegram) при падінні сайту

## Ліцензія

MIT
