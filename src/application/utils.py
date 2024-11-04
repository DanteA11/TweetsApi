"""Вспомогательные классы и функции."""

import logging
import queue
from logging.handlers import QueueHandler, QueueListener
from typing import Callable

from fastapi import FastAPI


def async_logger_init(
    name: str,
    level: int | str,
    formater: logging.Formatter,
    *handlers: logging.Handler,
    propagate: bool = False
) -> logging.Logger:
    """
    Инициализирует логер.

    Логер имеет единственный обработчик - "QueueHandler"
    (https://docs.python.org/3/library/logging.handlers.html#queuehandler).
    Сообщения направляются в очередь, откуда их забирает "QueueListener"
    (https://docs.python.org/3/library/logging.handlers.html#queuelistener)
    в отдельном потоке и распределяет сообщения по добавленным обработчикам.
    Это позволяет не блокировать поток выполнения при логировании.

    :param name: Имя логера.
    :param level: Уровень логирования.
    :param formater: Объект форматирования.
    :param handlers: Обработчики.
    :param propagate: Передавать ли записанные события
        обработчикам логера более высокого уровня.
    :return: Объект логера.
    """
    log_queue: queue.Queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(formater)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(queue_handler)
    logger.propagate = propagate

    queue_listener = QueueListener(log_queue, *handlers)
    queue_listener.start()

    return logger


def update_schema_name(app: FastAPI, function: Callable, name: str) -> None:
    """
    Update schema name.

    Updates the Pydantic schema name for a FastAPI function that takes
    in a fastapi.UploadFile = File(...) or bytes = File(...).

    This is a known issue that was reported on FastAPI#1442 in which
    the schema for file upload routes were auto-generated with no
    customization options. This renames the auto-generated schema to
    something more useful and clear.

    Args:
        app: The FastAPI application to modify.
        function: The function object to modify.
        name: The new name of the schema.


    https://github.com/fastapi/fastapi/discussions/9067
    """
    for route in app.routes:
        if route.endpoint is function:  # type: ignore
            route.body_field.type_.__name__ = name  # type: ignore
            break


class MetaSingleton(type):
    """Мета-класс, реализует паттерн синглтон."""

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        """Создание экземпляра класса."""
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]
