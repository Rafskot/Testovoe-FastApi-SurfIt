# Testovoe-FastApi-SurfIt
## Cтек технологий:
ЯП python версии 3.10  
Фреймворк FastAPI версии 0.108.0  
SQLAlchemy версии 1.4.51  
PostgreSQL версии 16.1  
## Развертывание проекта:
### Установка библиотек:
1. Откройте терминал и установите необходимые библиотеки, используя следующую команду:  
_pip install fastapi[all] sqlalchemy databases[postgresql]_
### Создание базы данных PostgreSQL
1. Установите PostgreSQL  
2. Создайте базу данных и пользователя, Используйте утилиту psql:  
_CREATE DATABASE mybase;_  
_CREATE USER tester WITH PASSWORD '12345';_  
_ALTER ROLE tester SET client_encoding TO 'utf8';_  
_ALTER ROLE tester SET default_transaction_isolation TO 'read committed';_  
_ALTER ROLE tester SET timezone TO 'UTC';_  
_GRANT ALL PRIVILEGES ON DATABASE mybase TO tester;_  
### Запуск FastAPI-проекта  
1. Запустите миграции:  
_psql -U postgres -d mybase_
2. Запустите FastAPI:  
_uvicorn your_app_name:app --reload_
3. Проверьте API:  
прейдети по ссылке: _http://127.0.0.1:8000/docs_
