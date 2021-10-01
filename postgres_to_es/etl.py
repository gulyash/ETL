import datetime

import psycopg2
import requests
from psycopg2.extras import DictCursor

from backoff import backoff
from config_reader import config
from state import State, JsonFileStorage


class Etl:
    def __init__(self) -> None:
        self.config = config
        self.state = State(JsonFileStorage(self.config.film_work_pg.state_file_path))
        self._fetch_query = None

    def run(self):
        for extracted in self.extract():
            transformed = self.transform(extracted)
            self.load(transformed)

    def _get_update_time(self, default_value=datetime.datetime(1970, 1, 1)):
        return self.state.get_state("last_updated_at") or default_value

    def _get_guery(self):
        if not self._fetch_query:
            with open("postgres_query.sql", "r") as query_file:
                self._fetch_query = query_file.read()
        return self._fetch_query

    @backoff()
    def extract(self, batch_size=100):
        query = self._get_guery()
        update_time = self._get_update_time()
        pg_conn = psycopg2.connect(
            **dict(self.config.film_work_pg.dsn), cursor_factory=DictCursor
        )

        with pg_conn.cursor() as cursor:
            cursor.execute(query, (update_time,))
            while True:
                batch = cursor.fetchmany(batch_size)
                if batch:
                    yield batch
                else: break
        cursor.close()

    def transform(self, extract):
        return [dict(row) for row in extract]

    def _post_index(self):
        with open("index.json", "r") as file:
            index = file.read()
        return requests.put(
            "http://127.0.0.1:9200/movies",
            data=index,
            headers={"Content-Type": "application/json"},
        )

    def load(self, transformed):
        self._post_index()
        print("*insert to elastic...*")
        self.state.set_state("last_updated_at", datetime.datetime(1970, 1, 1))


if __name__ == '__main__':
    Etl().run()
