![Build Status](https://github.com/daniltivodar/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# Foodgram

## Описание проекта
**Foodgram** — это сайт, на котором могут регистрироваться все пользователи, и добавлять рецепты своих любимых блюд! Также они могут делиться своими рецептами со всеми, и подсматривать идеи чужих рецептов. Добавлять эти рецепты в избранное, или список покупок(а также потом скачивать файл со всеми необходимыми ингредиентами для приготовления блюд). Пользователи могут подписываться на своих любимых авторов, а также отписываться от нелюбимых. На сайте есть удобное API, которым также удобно пользоваться как и сайтом.

## Функциональные возможности
- Регистрация и авторизация пользователей.
- Публикация рецептов пользователями: загрузка изображений, описания, списка ингридиентов.
- Добавление рецепотов в избранное и подписка на авторов рецептов.
- Формирование списка покупок на основе ингридиентов и его выгрузка в txt-файл.
- Админ-зона для управления контентом (фильтрация, скрытие, публикация и пр.)
- Предоставление данных через API.

## Стек технологий
- **Backend**: Python, Django, Django REST Framework, Gunicorn
- **Frontend**: React, JavaScript
- **База данных**: PostgreSQL
- **Сервер**: Nginx
- **Docker**: Docker, Docker Compose
- **DevOps**: GitHub Actions, DockerHub

## Локальное развертывание
### 1. Клонируйте репозиторий
```bash
git clone https://github.com/daniltivodar/foodgram-project-react.git
cd foodgram-project-react
```

### 2. Запустите фронтенд
```bash
cd frontend
npm i
npm run start
```

### 3. Запустите бэкенд (строго в новом терминале)
```bash
cd backend
python -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 4. Добавьте готовую базу ингредиентов и тегов для рецептов (опционально)
```bash
python manage.py import_ingredients
python manage.py import_tags
```

### 5. Создайте суперпользователя для управления админ-зоной:
```bash
python manage.py createsuperuser
```

## Развертывние на серере
### 1. Клонируйте репозиторий
```bash
git clone https://github.com/daniltivodar/foodgram-project-react.git
cd foodgram-project-react
```

### 2. Заполните переменные окружения
- `POSTGRES_DB`- имя базы данных.
- `POSTGRES_USER` - Имя пользователя бд.
- `POSTGRES_PASSWORD` - Пароль от бд.
- `DB_HOST` - хост.
- `DB_PORT`- порт.
- `ALLOWED_HOSTS` - разрешенные хосты.
- `DEBUG` - режим отладки приложения.
- `SECRET_KEY` - ключ безопасности приложения.
Пример заполнения есть в `env.example`.



### 3. Соберите и запустите контейнеры
При разработке используйте:
```bash
docker-compose up --build
```
При продакшене используйте:
```bash
docker-compose.production.yml up --build
```

### 4. Для развертывания DevOps-процессов на GitHub Actions (опционально)
В настройках секретов репозитория с приложением (Settings -> Secrets and variables -> Actions) создайте следующие переменные:
- `DOCKER_USERNAME` - имя пользователя на DockerHub.
- `DOCKER_PASSWORD` - пароль пользователя на DockerHub.
- `HOST` - IP-адрес удаленного сервера.
- `SSH_KEY` - ключ SSH-доступа к удаленному серверу.
- `USER` - логин SSH-доступа к удаленному серверу.
- `SSH_PASSPHRASE` - пароль SSH-доступа к удаленному серверу.
- `TELEGRAM_TO` - ID телеграм-аккаунта.
- `TELEGRAM_TOKEN` - токен Telegram-бота.


## Пример развернутого проекта
https://sickmoqchima.ddns.net/

#### Автор
Danil Tivodar
