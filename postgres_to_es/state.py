import abc
import datetime
import json
import time
from typing import Any, Optional


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
        self.date_format = "%Y-%m-%dT%H:%M:%S%z"

    def _get_prepared_state(self, state: dict):
        s = {**state}
        for k, v in s.items():
            if isinstance(v, datetime.datetime):

                s[k] = v.strftime(self.date_format)
        return s

    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        if self.file_path is None:
            return
        s = self._get_prepared_state(state)
        with open(self.file_path, "w") as file:
            json.dump(s, file)

    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        try:
            with open(self.file_path, "r") as file:
                result = json.load(file)
            return result
        except FileNotFoundError:
            return {}


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
