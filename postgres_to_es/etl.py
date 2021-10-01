import datetime

import psycopg2
from psycopg2.extras import DictCursor

from config_reader import config
from state import State, JsonFileStorage


class Etl:
    def __init__(self) -> None:
        self.config = config
        dsn = dict(self.config.film_work_pg.dsn)
        self.pg_conn = psycopg2.connect(**dsn, cursor_factory=DictCursor)
        self.state = State(JsonFileStorage(self.config.film_work_pg.state_file_path))

    def run(self):
        extracted = self.extract_records()
        transformed = self.transform(extracted)
        self.load(transformed)

    def _get_update_time(self, default_value=datetime.datetime(1970, 1, 1)):
        return self.state.get_state("last_updated_at") or default_value

    def extract_records(self):
        update_time = self._get_update_time()
        cursor = self.pg_conn.cursor()
        with open("postgres_query.sql", "r") as query_file:
            query = query_file.read()
        cursor.execute(query, (update_time,))
        res = [item for item in cursor]
        return res

    def transform(self, extract):
        return [dict(row) for row in extract]

    def load(self, transformed):
        print("*insert to elastic...*")
        self.state.set_state("last_updated_at", datetime.datetime.now())


Etl().run()
