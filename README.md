# Library Management API

REST API для управления библиотекой на Django Rest Framework.

Проект покрывает базовые процессы библиотеки: управление каталогом книг и экземпляров, авторами, жанрами, пользователями, а также учет выдачи и возврата книг. Для аутентификации используется JWT, для хранения данных - PostgreSQL, для контейнеризации - Docker Compose.

## Возможности

- регистрация и авторизация пользователей по JWT
- управление пользователями и профилем текущего пользователя
- CRUD для авторов, жанров и карточек книг
- учет физических экземпляров книг
- выдача и возврат книг через сущность `Loan`
- OpenAPI-документация через Swagger UI и ReDoc
- наполнение базы демонстрационными данными через `seed_demo_data`

## Технологии

- Python 3.13
- Django 6
- Django REST Framework
- PostgreSQL
- drf-spectacular
- django-filter
- Docker и Docker Compose
- Poetry

## Структура проекта

```text
config/                     настройки Django, URL и WSGI/ASGI
library/                    каталог книг, жанры, авторы, выдачи
library/management/commands/ management-команды проекта
users/                      кастомный пользователь, auth и API пользователей
docs/                       проектная документация и описание бизнес-процессов
Dockerfile                  сборка контейнера приложения
docker-compose.yml          запуск приложения и PostgreSQL
entrypoint.sh               ожидание БД, миграции, demo seed, старт сервера
pyproject.toml              зависимости Poetry
```

## Модель данных

Основные сущности проекта:

- `User` - кастомный пользователь с авторизацией по `email`
- `Author` - автор книги
- `Genre` - жанр книги
- `BookTitle` - карточка книги в каталоге
- `BookItem` - физический экземпляр книги
- `Loan` - выдача экземпляра книги пользователю

Подробные схемы и бизнес-правила описаны в `docs/models.md` и `docs/business-processes.md`.

## Переменные окружения

Проект использует `.env` в корне репозитория.

Минимальный пример:

```env
POSTGRES_DB=library_db
POSTGRES_USER=library_user
POSTGRES_PASSWORD=library_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Для Docker `POSTGRES_HOST` внутри контейнера приложения переопределяется как `db` через `docker-compose.yml`.

## Локальный запуск без Docker

1. Установить зависимости:

```bash
poetry install
```

2. Создать `.env` по примеру `.env.example`.

3. Поднять PostgreSQL и создать базу данных.

4. Применить миграции:

```bash
poetry run python manage.py migrate
```

5. Наполнить БД демонстрационными данными:

```bash
poetry run python manage.py seed_demo_data
```

6. Запустить сервер:

```bash
poetry run python manage.py runserver
```

## Запуск через Docker Compose

Основная команда запуска:

```bash
docker compose up --build
```

Что происходит при старте контейнера `web`:

- ожидание доступности PostgreSQL
- `python manage.py migrate`
- `python manage.py seed_demo_data`
- запуск Django на `0.0.0.0:8000`

Приложение будет доступно по адресу:

- `http://localhost:8000/api/docs/swagger/`
- `http://localhost:8000/api/docs/redoc/`
- `http://localhost:8000/api/schema/`

Данные PostgreSQL сохраняются в Docker volume `postgres_data`, поэтому не теряются при обычном `docker compose down`.

Если нужно удалить контейнеры вместе с данными БД:

```bash
docker compose down -v
```

## Полезные команды Docker

Запуск в фоне:

```bash
docker compose up --build -d
```

Просмотр логов:

```bash
docker compose logs -f
```

Выполнить management-команду внутри контейнера:

```bash
docker compose exec web python manage.py <command_name>
```

Например:

```bash
docker compose exec web python manage.py seed_demo_data
```

## Аутентификация и demo users

После выполнения `seed_demo_data` создаются демонстрационные пользователи:

- `admin@example.com` / `AdminPass123!`
- `reader@example.com` / `ReaderPass123!`

JWT можно получить через endpoint логина и затем передавать в заголовке:

```text
Authorization: Bearer <access_token>
```

## Документация API

Основные точки доступа:

- `GET /api/docs/swagger/` - Swagger UI
- `GET /api/docs/redoc/` - ReDoc
- `GET /api/schema/` - OpenAPI schema

API маршруты сгруппированы под префиксом `api/v1/`.

Список бизнес-эндпоинтов и трассировка требований находятся в `docs/endpoints.md`.

## Примеры функциональности

- `auth/register` и `auth/login` для регистрации и входа
- `authors`, `genres`, `books`, `book-items` для каталогизации фонда
- `loans` для выдачи, возврата и контроля статуса книги
- `users` и `users/me` для работы с учетными записями

## Management commands

В проекте используется management-команда:

- `seed_demo_data` - создать или обновить демонстрационные данные

Команда идемпотентна: повторный запуск обновляет тестовые записи и не должен бесконтрольно плодить дубликаты.


