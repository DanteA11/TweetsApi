"""
Функции для обеспечения логики работы приложения.

В основном модуле находятся модели SQLAlchemy и CrudController.
В подмодуле database - функции для подключения к базе данных.
"""

from ._models import *
from .crud import CrudController
