# LinkBiter

LinkBiter — сервис сокращения ссылок, построенный на **FastAPI**
Он позволяет создавать короткие ссылки, выполнять редирект на оригинальный URL, отслеживать статистику переходов и управлять ссылками

Сервис использует **PostgreSQL** для хранения данных и **Redis** для кэширования популярных запросов

---

# Описание API

API предоставляет следующие эндпоинты для работы со ссылками:

| Метод | Endpoint | Описание |
|------|---------|--------|
| POST | `/links/shorten` | Создание короткой ссылки |
| GET | `/links/{short_code}/stats` | Получение статистики ссылки |
| GET | `/links/search` | Поиск ссылки по оригинальному URL |
| GET | `/links/{short_code}` | Редирект на оригинальный URL |
| PUT | `/links/{short_code}` | Обновление короткой ссылки *(только для создателей ссылки)* |
| DELETE | `/links/{short_code}` | Удаление ссылки *(только для создателей ссылки)* |

Swagger-документация доступна после запуска: http://localhost:8000/docs

## Примеры запросов

### Создание короткой ссылки

```bash
curl -X 'POST' \
  'http://localhost:8000/links/shorten' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://zoom.com/",
    "custom_alias": "zoom",
    "expires_at": "2026-03-09T11:59:38.386Z"
    }'
```

Ответ:
```json
{
  "url": "https://zoom.com/",
  "short_code": "zoom",
  "short_url": "https://click.ru/zoom",
  "expires_at": "2026-03-09T11:59:38.386000Z"
}
```

### Получение статистики

```bash
curl -X 'GET' \
  'http://localhost:8000/links/zoom/stats' \
  -H 'accept: application/json'
```

Ответ:
```json
{
  "url": "https://zoom.com/",
  "created_at": "2026-03-09T11:14:25.486869Z",
  "clicks": 6,
  "last_used_at": "2026-03-09T11:15:10.500051Z"
}
```

### Поиск по оригинальному URL

```bash
curl -X 'GET' \
  'http://localhost:8000/links/search?original_url=https%3A%2F%2Fzoom.com%2F%20' \
  -H 'accept: application/json'
```

Ответ:
```json
{
  "url": "https://zoom.com/",
  "short_code": "zoom",
  "short_url": "https://click.ru/zoom",
  "expires_at": "2026-03-09T11:59:38.386000Z"
}
```

### Редирект

```bash
curl -X 'GET' \
  'http://localhost:8000/links/zoom' \
  -H 'accept: application/json'
```

### Обновление короткой ссылки

```bash
curl -X 'PUT' \
  'http://localhost:8000/links/zoom' \
  -H 'accept: application/json' \
  -H 'Authorization: тут будет bearer token'
  -H 'Content-Type: application/json' \
  -d '{
  "new_short_code": "zoom2"
}'
```

Ответ:
```json
{
  "url": "https://zoom.com/",
  "short_code": "zoom2",
  "short_url": "https://click.ru/zoom2",
  "expires_at": "2026-03-09T11:59:38.386000Z"
}
```

### Удаление короткой ссылки

```bash
curl -X 'DELETE' \
  'http://localhost:8000/links/zoom2' \
  -H 'accept: application/json' \
  -H 'Authorization: тут будет bearer token'
```

Ответ:
```json
{
  "detail": "Ссылка успешно удалена"
}
```

## Инструкция по запуску

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd linkbiter
   ```

2. Создайте файл `.env` со следующими переменными:
   ```
    DB_USER=postgres
    DB_PASS=postgres
    DB_HOST=db
    DB_PORT=5432
    DB_NAME=shortener

    REDIS_URL=redis://redis:6379/0
   ```

3. Запустите контейнеры:
   ```bash
    docker compose up --build
   ```

4. Примените миграции:
   ```bash
    docker exec -it linkbiter-api alembic upgrade head
   ```

5. API будет доступен: http://localhost:8000

6. Документация API: http://localhost:8000/docs

## Описание БД
Проект использует PostgreSQL для хранения данных.

Таблица `links`
| поле         | тип      | описание                       |
| ------------ | -------- | ------------------------------ |
| id           | integer  | идентификатор                  |
| short_code   | string   | короткий код ссылки            |
| short_url    | string   | короткая ссылка (доп поле)                |
| original_url | string   | оригинальный URL               |
| clicks       | integer  | количество переходов           |
| created_at   | datetime | дата создания                  |
| updated_at   | datetime | дата изменения                 |
| expires_at   | datetime | срок действия                  |
| last_used_at | datetime | последний переход              |
| created_by   | UUID     | пользователь, создавший ссылку |


Таблица `users`
| поле            | тип     | описание                       |
| --------------- | ------- | ------------------------------ |
| id              | UUID    | идентификатор пользователя     |
| email           | string  | email                          |
| hashed_password | string  | хэш пароля                     |
| is_active       | boolean | активен ли пользователь        |
| is_superuser    | boolean | является ли суперпользователем |
| is_verified     | boolean | подтвержден ли email           |

## Технологии

- `FastAPI` — веб-фреймворк
- `SQLAlchemy` — ORM
- `Alembic` — миграции БД
- `PostgreSQL` — база данных
- `Redis` — кэширование
- `Docker` — контейнеризация