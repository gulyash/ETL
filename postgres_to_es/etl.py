import datetime
import json
from typing import List, Generator

import psycopg2
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from psycopg2.extras import DictCursor, DictRow

from backoff import backoff
from config_reader import config
from state import State, JsonFileStorage


class Etl:
    def __init__(self) -> None:
        self.config = config
        self.state = State(JsonFileStorage(self.config.film_work_pg.state_file_path))
        self._fetch_query = None
        self.es = Elasticsearch()
        self.index_name = "movies"

    def run(self):
        for extracted in self.extract():
            transformed = self.transform(extracted)
            self.load(transformed)

    def _get_update_time(
        self, default_value: datetime.datetime = datetime.datetime(1970, 1, 1)
    ):
        return self.state.get_state("last_updated_at") or default_value

    def _get_guery(self):
        if not self._fetch_query:
            with open("postgres_query.sql", "r") as query_file:
                self._fetch_query = query_file.read()
        return self._fetch_query

    @backoff()
    def extract(self) -> Generator[List[DictRow], None, None]:
        query = self._get_guery()
        update_time = self._get_update_time()
        pg_conn = psycopg2.connect(
            **dict(self.config.film_work_pg.dsn), cursor_factory=DictCursor
        )

        with pg_conn.cursor() as cursor:
            cursor.execute(query, (update_time,))
            while True:
                batch = cursor.fetchmany(self.config.film_work_pg.limit)
                if not batch:
                    break
                yield batch
        cursor.close()

    def _transform_item(self, row: DictRow):
        item = dict(row)
        item.pop("updated_at")
        return {
            "_index": self.index_name,
            "_id": item.pop("fw_id"),
            **item
        }

    def transform(self, extract: List[DictRow]):
        return [self._transform_item(row) for row in extract]

    def _post_index(self):
        with open("index.json", "r") as file:
            index_body = json.load(file)
        self.es.indices.create(index=self.index_name, body=index_body, ignore=400)

    @backoff()
    def load(self, transformed):
        self._post_index()
        print("*insert to elastic...*")
        a = bulk(self.es, transformed)
        self.state.set_state("last_updated_at", datetime.datetime(1970, 1, 1))


if __name__ == "__main__":
    Etl().run()
