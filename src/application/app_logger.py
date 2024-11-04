"""Логер приложения."""

import sys
from logging import Formatter, StreamHandler

from .settings import get_settings
from .utils import async_logger_init

__settings = get_settings()
__handler = StreamHandler(sys.stdout)
__formatter = Formatter(
    fmt="%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s",
)


logger = async_logger_init(
    __settings.api_name, __settings.log_level, __formatter, __handler
)
