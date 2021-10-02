import json
import logging
import time
from pathlib import Path
from typing import List, Generator, Dict, Tuple

import psycopg2
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from psycopg2.extras import DictCursor, DictRow

from backoff import backoff
from config_reader import Config
from state import State, JsonFileStorage


logging.basicConfig(level=logging.INFO)


class MovieEtl:
    """Extract movies from PostgreSQL database and load them into ElasticSearch index"""

    def __init__(self, table_name, index_name) -> None:
        """Initiate ETL process with config values"""
        self.table_name = table_name
        self.index_name = index_name
        self._fetch_query = None
        self._index_body = None
        self.json_date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
        self.config = Config.parse_file("movie/config.json")
        self.state = State(JsonFileStorage(self.config.postgres.state_file_path))
        self.es = Elasticsearch(hosts=[self.config.elastic.elastic_host])

    def run(self):
        """Run extract -> transform -> load in a loop."""
        logging.info("Replication started.")
        while True:
            for extracted in self.extract():
                transformed, last_item_time = self.transform(extracted)
                self.load(transformed, last_item_time)
            time.sleep(self.config.postgres.fetch_delay)

    def _get_last_update_time(self, default_value: str = "2000-01-01T00:00:00.000000"):
        """Fetch last updated time from config to start up from"""
        return self.state.get_state("last_updated_at") or default_value

    def _get_guery(self, query_path: Path):
        """Load PostgreSQL filmwork query from file or use 'cached' one."""
        if not self._fetch_query:
            # file path validity is checked upon config validation
            with open(query_path, "r") as query_file:
                self._fetch_query = query_file.read()
        return self._fetch_query

    @backoff()
    def get_connection(self):
        """Obtain PostgreSQL database connection using a backoff."""
        return psycopg2.connect(
            **dict(self.config.postgres.dsn), cursor_factory=DictCursor
        )

    def extract(self) -> Generator[List[DictRow], None, None]:
        """Fetch movies data from PostgreSQL in batches"""
        query = self._get_guery(self.config.postgres.sql_query_path)
        update_time = self._get_last_update_time()
        pg_conn = self.get_connection()
        with pg_conn.cursor() as cursor:
            # When we update genre or a person `updated_at` column of related movies gets a new value.
            # This allows us to fetch everything we need using the same query.
            # See signals.py in Django application for reference.
            cursor.execute(query, (update_time,))
            while True:
                batch = cursor.fetchmany(self.config.postgres.limit)
                if not batch:
                    break
                yield batch
        cursor.close()

    def _transform_item(self, row: DictRow):
        """Convert DictRow into ElasticSearch consumable dictionary."""
        item = dict(row)
        del item["updated_at"]
        return {
            "_index": self.index_name,
            "_id": item.pop("fw_id"),
            **item,
        }

    def _get_update_time(self, last_item: DictRow) -> str:
        """Get updated_at time of hte item in the format of a json-consumable string"""
        last_datetime = dict(last_item)["updated_at"]
        return last_datetime.strftime(self.json_date_format)

    def transform(self, extract: List[DictRow]) -> Tuple[List[Dict], str]:
        """Prepare data for loading into ElasticSearch and get last item's updated_at time."""
        last_item_time = self._get_update_time(extract[-1])
        transformed = [self._transform_item(row) for row in extract]
        return transformed, last_item_time

    def _post_index(self):
        """Create filmwork index in ElasticSearch.
        No error is raised if index already exists."""
        if not self._index_body:
            with open(self.config.elastic.index_json_path, "r") as file:
                self._index_body = json.load(file)

        self.es.indices.create(
            index=self.index_name, body=self._index_body, ignore=400
        )

    @backoff()
    def load(self, transformed: List[Dict], last_item_time: str):
        """Insert data into ElasticSearch and save new state on success."""
        self._post_index()
        bulk(self.es, transformed)
        self.state.set_state("last_updated_at", last_item_time)
        logging.info("Batch of %s movies uploaded to elasticsearch.", len(transformed))


if __name__ == "__main__":
    MovieEtl("film_work", "movies").run()
