import os
import sqlite3
from dataclasses import fields, astuple
from typing import TypeVar, Type, List

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from sqlite_to_postgres.schemas import (
    Movie,
    Genre,
    Person,
    GenreFilmWork,
    PersonFilmWork,
)

Replicable = TypeVar("Replicable", Movie, Genre, Person, GenreFilmWork, PersonFilmWork)


class PostgresSaver:
    def __init__(self, _connection: _connection) -> None:
        self.pg_conn = _connection

    def generate_mogrified_tuples(
        self, row_format_string: str, items: List[Replicable], cursor: DictCursor
    ):
        for item in items:
            t = astuple(item)
            mogrified_row = cursor.mogrify(row_format_string, t).decode()
            yield mogrified_row

    def insert_table(self, model_class: Type[Replicable], items: List[Replicable]):
        field_names = list(x.name for x in fields(model_class))
        placeholders = ", ".join("%s" for _ in range(len(field_names)))
        row_format_string = f"({placeholders})"

        cursor = self.pg_conn.cursor()
        tuples = self.generate_mogrified_tuples(row_format_string, items, cursor)

        all_rows = ",".join(tuples)
        columns = ", ".join(field_names)
        query = f"""INSERT INTO content.{model_class.target_table} ({columns})
                    VALUES {all_rows} on conflict do nothing
                    """
        cursor.execute(query)

    def save_all_data(self, data: dict):
        for model_class in data:
            self.insert_table(model_class, data[model_class])


class SQLiteLoader:
    models_to_replicate = [Person, Genre, Movie, GenreFilmWork, PersonFilmWork]

    def __init__(self, sqlite_conn: sqlite3.Connection) -> None:
        self.connection = sqlite_conn

    def get_model_items(self, model: Type[Replicable]):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {model.source_table}")
        result = [model(*item) for item in cursor]
        return result

    def load_movies(self):
        result = {
            model: self.get_model_items(model) for model in self.models_to_replicate
        }
        return result


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    data = sqlite_loader.load_movies()
    postgres_saver.save_all_data(data)


if __name__ == "__main__":
    dsl = {
        "dbname": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
    }
    sqlite_conn = sqlite3.connect("db.sqlite")
    pg_conn = psycopg2.connect(**dsl, cursor_factory=DictCursor)
    with sqlite_conn, pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
    sqlite_conn.close()
    pg_conn.close()
