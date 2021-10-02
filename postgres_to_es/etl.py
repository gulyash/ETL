import datetime
import json
import logging
import time
from typing import List, Generator, Dict

import psycopg2
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from psycopg2.extras import DictCursor, DictRow

from backoff import backoff
from config_reader import config
from state import State, JsonFileStorage


logging.basicConfig(level=logging.INFO)


class Etl:
    """Extract movies from PostgreSQL database and load them into ElasticSearch index"""

    def __init__(self) -> None:
        """Initiate ETL process with config values"""
        self.config = config
        self.state = State(JsonFileStorage(self.config.film_work_pg.state_file_path))
        self._fetch_query = None
        self.es = Elasticsearch(hosts=[self.config.elastic.elastic_host])

    def run(self):
        """Run extract -> transform -> load in a loop."""
        while True:
            for extracted in self.extract():
                transformed, last_item_time = self.transform(extracted)
                self.load(transformed, last_item_time)
            time.sleep(self.config.film_work_pg.fetch_delay)

    def _get_last_update_time(
        self, default_value: datetime.datetime = datetime.datetime(1970, 1, 1)
    ):
        """Fetch last updated time from config to start up from"""
        return self.state.get_state("last_updated_at") or default_value

    def _get_guery(self):
        """Load PostgreSQL filmwork query from file or use 'cached' one."""
        if not self._fetch_query:
            with open(self.config.film_work_pg.sql_query_path, "r") as query_file:
                self._fetch_query = query_file.read()
        return self._fetch_query

    @backoff()
    def get_connection(self):
        """Obtain PostgreSQL database connection using a backoff."""
        return psycopg2.connect(
            **dict(self.config.film_work_pg.dsn), cursor_factory=DictCursor
        )

    def extract(self) -> Generator[List[DictRow], None, None]:
        """Fetch movies data from PostgreSQL in batches"""
        query = self._get_guery()
        update_time = self._get_last_update_time()
        pg_conn = self.get_connection()
        with pg_conn.cursor() as cursor:
            # When we update genre or a person `updated_at` column of related movies gets a new value.
            # This allows us to fetch everything we need using the same query.
            # See signals.py in Django application for reference.
            cursor.execute(query, (update_time,))
            while True:
                batch = cursor.fetchmany(self.config.film_work_pg.limit)
                if not batch:
                    break
                yield batch
        cursor.close()

    def _transform_item(self, row: DictRow):
        """Convert DictRow into ElasticSearch consumable dictionary."""
        item = dict(row)
        del item["updated_at"]
        return {
            "_index": self.config.elastic.index_name,
            "_id": item.pop("fw_id"),
            **item,
        }

    def transform(self, extract: List[DictRow]):
        """Prepare data for loading into ElasticSearch and get last item's updated_at time."""
        last_item_time = dict(extract[-1])["updated_at"]
        return [self._transform_item(row) for row in extract], last_item_time

    def _post_index(self):
        """Create filmwork index in ElasticSearch.
        No error is raised if index already exists."""
        with open(self.config.elastic.index_json_path, "r") as file:
            index_body = json.load(file)
        self.es.indices.create(
            index=self.config.elastic.index_name, body=index_body, ignore=400
        )

    @backoff()
    def load(self, transformed: List[Dict], last_item_time: datetime.datetime):
        """Insert data into ElasticSearch and save new state on success."""
        self._post_index()
        bulk(self.es, transformed)
        self.state.set_state("last_updated_at", last_item_time)
        logging.info(f"Batch of {len(transformed)} movies uploaded to elasticsearch.")


if __name__ == "__main__":
    Etl().run()
