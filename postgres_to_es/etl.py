import abc
import json
from typing import Any, Optional

import psycopg2
from psycopg2.extras import DictCursor

from config_reader import config


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        if self.file_path is None:
            return

        with open(self.file_path, "w") as file:
            json.dump(state, file)

    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        try:
            with open(self.file_path, "r") as file:
                result = json.load(file)
            return result
        except FileNotFoundError:
            return {}


class PostgresStorage(BaseStorage):
    def __init__(self) -> None:
        self.config = config
        self.connection = psycopg2.connect(**dict(self.config.film_work_pg.dsn), cursor_factory=DictCursor)

    def retrieve_state(self) -> dict:

        pass

    def save_state(self, state: dict) -> None:
        pass


class State:
    """
    Класс для хранения состояния при работе с данными, чтобы постоянно не перечитывать данные с начала.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.state = self.storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        self.state[key] = value
        self.storage.save_state(self.state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        return self.state.get(key, None)
