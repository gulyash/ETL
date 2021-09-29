import inspect
import json
import re
import sys
import tempfile
from json import JSONDecodeError


from functools import wraps

from postgres_to_es.state import JsonFileStorage, State


def test_get_empty_state():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b'{}')
        f.seek(0)

        storage = JsonFileStorage(f.name)
        state = State(storage)

        try:
            result = state.get_state('key')
        except Exception as e:
            assert False, f'По несуществующему ключу должен отдаваться None'

        assert result is None, 'Получение пустого состояния из файла произошло с ошибками'


def test_save_new_state():
    file_name = tempfile.mktemp()
    storage = JsonFileStorage(file_name)
    state = State(storage)

    try:
        state.set_state('key', 123)
    except Exception as e:
        assert False, f'Ошибка установки состояния: {e}'

    with open(file_name) as f:
        try:
            data = json.load(f)
        except:
            assert False, 'Не удалось загрузить состояние из JSON'
        assert data == {'key': 123}, 'Сохранить состояние в файл не удалось. Ожидались другие данные.'


def test_retrieve_existing_state():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b'{"key": 10}')
        f.seek(0)

        storage = JsonFileStorage(f.name)
        state = State(storage)

        assert state.get_state('key') == 10, 'Достать правильное состояние из файла не удалось'


def test_save_state_and_retrieve():
    file_name = tempfile.mktemp()
    storage = JsonFileStorage(file_name)
    state = State(storage)

    state.set_state('key', 123)

    # Принудительно удаляем объекты
    del state
    del storage

    storage = JsonFileStorage(file_name)
    state = State(storage)

    assert state.get_state('key') == 123, 'Сохранение состояния, а затем и его загрузка прошли неудачно'


def platform_exc(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AssertionError as e:
            raise e
        except Exception as e:
            assert False, f'Возникла ошибка: {repr(e)}'

    return inner


@platform_exc
def run_tests():
    test_get_empty_state()
    test_save_new_state()
    test_retrieve_existing_state()
    test_save_state_and_retrieve()


run_tests()
