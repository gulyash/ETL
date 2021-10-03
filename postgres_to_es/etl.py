import json
import logging
import time
from abc import abstractmethod, ABC
from typing import List, Generator, Dict, Tuple

import psycopg2
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from psycopg2.extras import DictCursor, DictRow

from backoff import backoff
from config_reader import config
from movies.movies_query import movies_query
from state import State, JsonFileStorage

logging.basicConfig(level=logging.INFO)


class Etl(ABC):
    """General Etl class for item replication from PostgreSQL database to ElasticSearch index"""

    def __init__(self, index_name: str) -> None:
        """Initiate ETL process with config values"""
        self.index_name = index_name
        self.json_date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
        self._index_body = None
        self.order_field = self.state_field = "updated_at"
        self.state = State(JsonFileStorage(config.state.file_path))
        self.es = Elasticsearch(hosts=[config.elastic.elastic_host])

    def run(self):
        """Run extract -> transform -> load in a loop."""
        logging.info("Replication started.")
        while True:
            for extracted in self.extract():
                transformed, last_item_time = self.transform(extracted)
                self.load(transformed)
                self.state.set_state(self.state_field, last_item_time)
                time.sleep(config.postgres.fetch_delay)

    def extract(self) -> Generator[List[DictRow], None, None]:
        """Fetch movies data from PostgreSQL in batches"""
        update_time = self._get_last_update_time()
        pg_conn = self.get_connection()
        with pg_conn.cursor() as cursor:
            # When we update genre or a person `updated_at` column of related movies gets a new value.
            # This allows us to fetch everything we need using the same query.
            # See signals.py in Django application for reference.
            cursor.execute(self._get_guery(), (update_time,))
            while True:
                batch = cursor.fetchmany(config.postgres.limit)
                if not batch:
                    break
                yield batch
        cursor.close()

    @abstractmethod
    def _get_guery(self):
        """Load PostgreSQL query from file or use 'cached' one."""
        pass

    def _get_last_update_time(self, default_value: str = "2000-01-01T00:00:00.000000"):
        """Fetch last updated time from config to start up from"""
        return self.state.get_state(self.state_field) or default_value

    @backoff()
    def get_connection(self):
        """Obtain PostgreSQL database connection using a backoff."""
        return psycopg2.connect(**dict(config.postgres.dsn), cursor_factory=DictCursor)

    def transform(self, extract: List[DictRow]) -> Tuple[List[Dict], str]:
        """Prepare data for loading into ElasticSearch and get last item's updated_at time."""
        last_item_time = self._get_update_time(extract[-1])
        transformed = [self._transform_item(row) for row in extract]
        return transformed, last_item_time

    def _transform_item(self, row: DictRow):
        """Convert DictRow into ElasticSearch consumable dictionary."""
        item = dict(row)
        del item[self.order_field]
        return {
            "_index": self.index_name,
            "_id": item.pop("id"),
            **item,
        }

    def _get_update_time(self, last_item: DictRow) -> str:
        """Get `updated_at` of the item in the format of a json-consumable string"""
        last_datetime = dict(last_item)[self.order_field]
        return last_datetime.strftime(self.json_date_format)

    @backoff()
    def load(self, transformed: List[Dict]):
        """Insert data into ElasticSearch and save new state on success."""
        self._post_index()
        bulk(self.es, transformed)
        logging.info(
            "Batch of %s %s uploaded to elasticsearch.",
            len(transformed),
            self.index_name,
        )

    def _post_index(self):
        """Create index in ElasticSearch. No error is raised if index already exists."""
        if not self._index_body:
            with open(config.elastic.index_json_path, "r") as file:
                self._index_body = json.load(file)

        self.es.indices.create(
            index=self.index_name, body=self._index_body, ignore=400
        )


class MovieEtl(Etl):
    """Extract movies from PostgreSQL database and load them into ElasticSearch index"""

    def _get_guery(self):
        return movies_query

    def __init__(self) -> None:
        """Specifies config file and item name for generic ETL"""
        super().__init__(index_name="movies")


if __name__ == "__main__":
    MovieEtl().run()
