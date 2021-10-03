import datetime
import logging
import time
from functools import wraps

logging.basicConfig(level=logging.INFO)


def backoff(
    start_sleep_time=0.1,
    factor=2,
    border_sleep_time=10,
    timeout=datetime.timedelta(minutes=1),
):
    """
    Функция для повторного выполнения функции через некоторое время, если возникла ошибка. Использует наивный экспоненциальный рост времени повтора (factor) до граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time
    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :param timeout: максимальное суммарное время ожидания, после которого ошибка будет передана дальше.
    :return: результат выполнения функции
    """
    def get_sleep_time(n):
        time_interval = start_sleep_time * factor ** n
        return (
            border_sleep_time
            if time_interval >= border_sleep_time
            else time_interval
        )

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            n = 0
            total_sleep_time = datetime.timedelta(seconds=0)
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if total_sleep_time > timeout:
                        logging.warning(
                            "Encountered error was not resolved in %s, raising...",
                            str(timeout),
                        )
                        raise e

                    sleep_time = get_sleep_time(n)
                    logging.info(
                        "Oh no, an error! I guess I'll take a %s sec nap...", sleep_time
                    )
                    time.sleep(sleep_time)
                    total_sleep_time += datetime.timedelta(seconds=sleep_time)
                    n += 1

        return inner

    return func_wrapper
