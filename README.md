![Build Status](https://github.com/daniltivodar/recipe-api-service/actions/workflows/main.yml/badge.svg)(https://github.com/daniltivodar/recipe-api-service/actions)
[![Python 3.9](https://img.shields.io/badge/Python-3.9-blue.svg)](https://www.python.org/)
[![Django 4.2](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![DRF 3.15](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)

# Recipe API Service

Современный API-сервис для обмена кулинарными рецептами с расширенными возможностями социального взаимодействия.

## Возможности

### Основной функционал
- Публикация рецептов - Создавайте и делитесь своими кулинарными творениями
- Умный поиск - Фильтрация рецептов по тегам, автору и ингредиентам
- Социальные взаимодействия - Подписки на авторов и оценка рецептов

### Персональные коллекции
- Избранное - Сохраняйте понравившиеся рецепты в персональную коллекцию
- Корзина покупок - Формируйте список ингредиентов для выбранных рецептов
- Экспорт списка - Скачивайте список покупок в удобном формате

### Социальные функции
- Система подписок - Следите за любимыми авторами
- Лента рецептов - Персонализированная подборка от авторов на которых вы подписаны
- Теги и категории - Удобная навигация по кулинарным направлениям

## Технологический стек

- Python 3.9 - Бэкенд язык программирования
- Django 4.2 - Веб-фреймворк
- Django REST Framework 3.15 - REST API framework
- Simple JWT - Аутентификация
- PostgreSQL - База данных
- Docker - Контейнеризация
- Nginx - Веб-сервер
- GitHub Actions - CI/CD

## Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Python 3.9+ (для разработки)

### Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/daniltivodar/recipe-api-service.git
cd recipe-api-service
```

2. Настройте окружение:
```bash
cp env.example .env
Отредактируйте .env файл по необходимости
```

3. Запустите сервис:
```bash
docker-compose -f docker-compose.production.yml up --build
```

## Загрузка данных

### Импорт тегов
```bash
docker-compose exec backend python manage.py import_tags
```

### Импорт ингредиентов
```bash
docker-compose exec backend python manage.py import_ingredients
```

## Документация API

После запуска сервиса документация API доступна по адресам:
- Swagger: /swagger/
- ReDoc: /redoc/
- DRF Browserable API: /api/

## Разработчик

Данил Тиводар
[GitHub Profile](https://github.com/daniltivodar)
