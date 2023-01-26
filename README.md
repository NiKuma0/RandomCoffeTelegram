# Random coffee telegram bot

Этот бот предназначен для поиска пар между студентам HR и IT специалистов.

# Стек
* [Python](https://python.org)
* [aiogram 3](https://github.com/aiogram/aiogram/tree/dev-3.x)
* PostgreSQL
* [peewee](https://github.com/coleifer/peewee)
* [Docker](https://docker.com)
# Развертывание
Предварительно проверяем наличие Docker и docker-compose-а.

1. Создайте файл `.env`, заполните его примерно как в файле `.env_example`.
2. В ту же папку переместите файл `docker-compose.yaml`.
3. Запускаем!
    ```shell
    sudo docker-compose up
    ```
# Сборка докера локально
1. Клонируем репозиторий:
    ```shell
    git clone https://github.com/NiKuma0/RandomCoffeTelegram
    ```
2. Переходим в папку `app/`
    ```shell
    cd app/
    ```
3. Запускаем сборку:
    ```shell
    sudo docker build .
    ```

# Запуск проекта без докера
1. Клонируем репозиторий:
    ```shell
    git clone https://github.com/NiKuma0/RandomCoffeTelegram
    ```
2. В файле `app/config.py` измените переменную `TESTING` на `True`, 
если хотите использовать SQLite вместо Postegres. В другом случае не 
забудьте добавить настройки в окружение 
(те же, что в файле `.env_example`).
3. Запускаем командой:
    ```shell
    cd app; python main.py
    ```