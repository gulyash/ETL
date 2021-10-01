import psycopg2
from psycopg2.extras import DictCursor

from config_reader import config
from state import State, JsonFileStorage


class Extractor:
    def __init__(self) -> None:
        self.state = State(JsonFileStorage("state.json"))
        self.config = config

        dsn = dict(self.config.film_work_pg.dsn)
        self.connection = psycopg2.connect(**dsn, cursor_factory=DictCursor)

    def extract(self):
        self.extract_records()

    def extract_records(self):
        cursor = self.connection.cursor()
        filmwork_ids = ("3d825f60-9fff-4dfe-b294-1a45fa1e115d",)
        cursor.execute("""SELECT
                fw.id as fw_id,
                fw.title,
                fw.description,
                fw.rating as imdb_rating,
                ARRAY_AGG(DISTINCT g.name) AS genre,
                ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'director') AS director,
                JSON_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) FILTER (WHERE pfw.role = 'actor') AS actors,
                JSON_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) FILTER (WHERE pfw.role = 'writer') AS writers,
                ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'actor') AS actors_names,
                ARRAY_AGG(DISTINCT p.full_name) FILTER (WHERE pfw.role = 'writer') AS writers_names
            FROM content.film_work fw
            LEFT OUTER JOIN content.genre_film_work gfw ON fw.id = gfw.film_work_id
            LEFT OUTER JOIN content.genre g ON (gfw.genre_id = g.id)
            LEFT OUTER JOIN content.person_film_work pfw ON (fw.id = pfw.film_work_id)
            LEFT OUTER JOIN content.person p ON (pfw.person_id = p.id)
            WHERE fw.id IN %s
            GROUP BY fw.id, fw.title, fw.description, fw.rating
            ORDER BY fw.updated_at;
            """, (filmwork_ids,))
        res = [item for item in cursor]
        return res


def extract_from_postgres():
    extractor = Extractor()
    return extractor.extract_records()


def transform(extract):
    return [dict(row) for row in extract]


def load_to_elastic(transformed):
    pass


def run_etl():
    extracted = extract_from_postgres()
    transformed = transform(extracted)
    load = load_to_elastic(transformed)


run_etl()
