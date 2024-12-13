# Сервис микроблогов
Предоставляет пользователям возможности для публикации коротких текстовых сообщений 
у себя на странице и отслеживания сообщений других пользователей. Кроме того пользователи могут 
оставлять реакцию "Нравится" под сообщениями.

## Сервис
Сервис будет доступен по пути: `/`

## Установка
1. Скачать репозиторий можно с помощью команды: `git clone 'ссылка на репозиторий'`.
2. Запуск осуществляется через [Docker](https://docs.docker.com/engine/install/).
3. Для работы приложения необходимо установить переменные окружения:
    ```properties
    # Настройки Postgres
    POSTGRES_USER=имя пользователя
    POSTGRES_PASSWORD=пароль
    POSTGRES_HOSTNAME=имя хоста
    POSTGRES_DB=название базы данных
    POSTGRES_CONTAINER_NAME=postgres # имя контейнера
    # Настройки приложения 
    MAX_IMAGE_SIZE=10485760 # максимальный размер изображения в байтах
    API_NAME=TweetsApi # имя api для документации
    LOG_LEVEL=INFO # уровень логирования
    PORT=порт для запуска
    APP_CONTAINER_NAME=app # имя контейнера
    ```
   Переменные можно передать при запуске контейнера, либо добавить в файл `.env` рядом с 
файлом `docker-compose.yml`
4. Для запуска необходимо перейти в папку с файлом `docker-compose.yml` и ввести команду:
```shell
docker compose up
```
## Документация
Документация API будет доступна после запуска по пути: `/api/docs`.
## Тестирование
Тесты можно запустить локально или внутри контейнера.
### Локально:
1. В файле `docker-compose.yml` нужно закомментировать следующее:
    ```yaml
      #app:
      #  build:
      #    context: src
      #  container_name: ${APP_CONTAINER_NAME}
      #  depends_on:
      #    - ${POSTGRES_HOSTNAME}
      #  environment:
      #    - DATABASE_URL=postgresql+psycopg_async://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOSTNAME}/${POSTGRES_DB}
      #    - MAX_IMAGE_SIZE=${MAX_IMAGE_SIZE}
      #    - MEDIA_PATH=static/medias
      #   - API_NAME=${API_NAME}
      #    - LOG_LEVEL=${LOG_LEVEL}
      #  stop_signal: SIGKILL
      #  restart: on-failure
      #  ports:
      #   - ${PORT}:80
      #  networks:
      #    - postgres
      #  volumes:
      #   - ./src/static/medias/:/app/static/medias
    ```
2. Создаем и активируем [виртуальное окружение](https://docs.python.org/3/tutorial/venv.html).
3. В директории src находим файл `.env` и устанавливаем в нем адрес тестовой базы данных:
    ```properties
    DATABASE_URL=postgresql+psycopg_async://{ваш логин}:{ваш пароль}@localhost/postgres
    ```
4. Запускаем базу данных:
    ```shell
   docker compose up
    ```
5. Переходим в директорию src и устанавливаем библиотеки.
    ```shell
   cd src
   pip install -r requirements.txt
   pip install -r requirements_test.txt
    ```
6. Запускаем тесты:
    ```shell
   pytest
    ```
### В контейнере:
1. В директории с файлом `docker-compose.yml` создаем файл `.env`, как было 
указано в разделе "Установка", если он еще не был создан. В нем необходимо изменить
название базы данных:
    ```properties
    POSTGRES_DB=postgres
   # база данных postgres создается по умолчанию, так как она не 
   # используется во время работы приложения, ее можно использовать
   # для тестов.
    ```
2. Запускаем контейнеры:
    ```shell
   docker compose up --build
   ```
3. Входим в контейнер с приложением:
   ```shell
   docker exec -ti 'имя или id контейнера' /bin/bash
   ```
4. Устанавливаем библиотеки:
   ```shell
   pip install -r requirements_test.txt
   ```
5. Запускаем тесты:
   ```shell
   pytest
   ```

