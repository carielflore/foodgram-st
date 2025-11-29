# Foodgram Backend

Бэкенд для проекта Foodgram - социальной сети для публикации рецептов.

## Описание

Foodgram - это веб-приложение, где пользователи могут:
- Публиковать рецепты с фотографиями
- Добавлять рецепты в избранное
- Подписываться на других авторов
- Создавать список покупок и скачивать его
- Фильтровать рецепты по тегам и авторам

## Технологический стек

- **Python 3.10.19**
- **Django 4.2.16**
- **Django REST Framework 3.14.0**
- **Djoser 2.2.3** - аутентификация и регистрация
- **PostgreSQL** - база данных
- **Gunicorn** - WSGI сервер
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - веб-сервер и reverse proxy

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- Git

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd foodgram-st/backend
```

### 2. Создание .env файла

Скопируйте `.env.example` в `.env` и заполните переменные окружения:

```bash
cp .env.example .env
```

Пример `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=foodgram
DB_USER=foodgram_user
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_secure_password
```

### 3. Запуск с помощью Docker Compose

Из директории `infra/`:

```bash
cd ../infra
docker-compose up -d
```

Это запустит все сервисы:
- PostgreSQL (база данных)
- Backend (Django API)
- Frontend (React SPA)
- Nginx (веб-сервер)

### 4. Загрузка данных

После первого запуска загрузите ингредиенты в базу данных:

```bash
docker-compose exec backend python manage.py load_ingredients
```

### 5. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```

### 6. Доступ к приложению

- **Фронтенд**: http://localhost
- **API**: http://localhost/api/
- **Админка**: http://localhost/admin/
- **Документация API**: http://localhost/api/docs/

## Разработка

### Локальный запуск (без Docker)

1. Создайте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Настройте `.env` для локальной разработки (используйте SQLite):

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

4. Выполните миграции:

```bash
python manage.py migrate
```

5. Загрузите данные:

```bash
python manage.py load_ingredients
```

6. Создайте суперпользователя:

```bash
python manage.py createsuperuser
```

7. Запустите сервер разработки:

```bash
python manage.py runserver
```

## Структура проекта

```
backend/
├── foodgram/              # Основной проект Django
│   ├── settings.py        # Настройки проекта
│   ├── urls.py            # Главный URL конфиг
│   └── wsgi.py            # WSGI приложение
├── recipes/               # Приложение для рецептов
│   ├── models.py          # Модели: Recipe, Ingredient, Tag
│   ├── admin.py           # Настройка админки
│   └── management/        # Management команды
│       └── commands/
│           └── load_ingredients.py
├── users/                 # Приложение для пользователей
│   ├── models.py          # Модели: User, Subscription
│   └── admin.py           # Настройка админки
├── api/                   # API приложение
│   ├── serializers.py     # Сериализаторы DRF
│   ├── views.py           # ViewSets
│   ├── urls.py            # URL роутинг
│   ├── permissions.py     # Права доступа
│   ├── pagination.py      # Пагинация
│   └── fields.py          # Кастомные поля (Base64ImageField)
├── requirements.txt       # Python зависимости
├── Dockerfile             # Docker образ
└── manage.py              # Django management скрипт
```

## API Эндпоинты

### Пользователи

- `GET /api/users/` - список пользователей
- `POST /api/users/` - регистрация
- `GET /api/users/{id}/` - профиль пользователя
- `GET /api/users/me/` - текущий пользователь
- `PUT /api/users/me/avatar/` - установить аватар
- `DELETE /api/users/me/avatar/` - удалить аватар
- `GET /api/users/subscriptions/` - мои подписки
- `POST /api/users/{id}/subscribe/` - подписаться
- `DELETE /api/users/{id}/subscribe/` - отписаться

### Аутентификация

- `POST /api/auth/token/login/` - получить токен
- `POST /api/auth/token/logout/` - удалить токен

### Рецепты

- `GET /api/recipes/` - список рецептов
- `POST /api/recipes/` - создать рецепт
- `GET /api/recipes/{id}/` - детали рецепта
- `PATCH /api/recipes/{id}/` - обновить рецепт
- `DELETE /api/recipes/{id}/` - удалить рецепт
- `GET /api/recipes/{id}/get-link/` - короткая ссылка
- `POST /api/recipes/{id}/favorite/` - в избранное
- `DELETE /api/recipes/{id}/favorite/` - из избранного
- `POST /api/recipes/{id}/shopping_cart/` - в список покупок
- `DELETE /api/recipes/{id}/shopping_cart/` - из списка покупок
- `GET /api/recipes/download_shopping_cart/` - скачать список

### Ингредиенты и теги

- `GET /api/ingredients/` - список ингредиентов
- `GET /api/ingredients/{id}/` - детали ингредиента
- `GET /api/tags/` - список тегов
- `GET /api/tags/{id}/` - детали тега

## Management команды

### Загрузка ингредиентов

```bash
# Из JSON (по умолчанию)
python manage.py load_ingredients

# Из CSV
python manage.py load_ingredients --file data/ingredients.csv

# С очисткой таблицы перед загрузкой
python manage.py load_ingredients --clear
```

## Тестирование

### С помощью Postman

1. Импортируйте коллекцию из `postman_collection/`
2. Настройте переменные окружения:
   - `base_url`: http://localhost/api
   - `token`: (заполнится после авторизации)
3. Запустите тесты

## Деплой

### Подготовка

1. Соберите Docker образ:

```bash
docker build -t username/foodgram-backend:latest .
```

2. Запушьте в Docker Hub:

```bash
docker push username/foodgram-backend:latest
```

### На сервере

1. Скопируйте файлы на сервер:
   - `infra/docker-compose.yml`
   - `infra/nginx.conf`
   - `backend/.env`

2. Запустите контейнеры:

```bash
docker-compose up -d
```

3. Выполните миграции и соберите статику:

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
docker-compose exec backend python manage.py load_ingredients
```

4. Создайте суперпользователя:

```bash
docker-compose exec backend python manage.py createsuperuser
```

## CI/CD

Проект настроен для работы с GitHub Actions. При push в ветку `main`:

1. Запускаются тесты
2. Собирается Docker образ
3. Образ пушится в Docker Hub
4. (Опционально) Автоматический деплой на сервер

## Полезные команды Docker

```bash
# Просмотр логов
docker-compose logs -f backend

# Перезапуск сервисов
docker-compose restart

# Остановка
docker-compose down

# Остановка с удалением volumes
docker-compose down -v

# Выполнение команд в контейнере
docker-compose exec backend python manage.py <command>

# Доступ к shell
docker-compose exec backend python manage.py shell

# Доступ к PostgreSQL
docker-compose exec db psql -U foodgram_user -d foodgram
```

## Troubleshooting

### Проблемы с миграциями

```bash
docker-compose exec backend python manage.py migrate --fake-initial
```

### Проблемы с правами на файлы

```bash
docker-compose exec backend chown -R $(id -u):$(id -g) /app/media
```

### Пересоздание базы данных

```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

## Лицензия

[Укажите вашу лицензию]

## Авторы

[Ваше имя]

## Контакты

[Ваши контакты]
