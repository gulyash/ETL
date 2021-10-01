import datetime
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class Movie:
    source_table = "film_work"
    target_table = "film_work"

    id: uuid.UUID
    title: str
    description: str
    creation_date: datetime.date
    certificate: str
    file_path: str
    rating: float
    type: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(frozen=True)
class Genre:
    source_table = "genre"
    target_table = "genre"

    id: uuid.UUID
    name: str
    description: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(frozen=True)
class Person:
    source_table = "person"
    target_table = "person"

    id: uuid.UUID
    full_name: str
    birth_date: datetime.date
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(frozen=True)
class GenreFilmWork:
    target_table = "genre_film_work"
    source_table = "genre_film_work"

    id: uuid.UUID
    film_work_id: uuid.UUID
    genre_id: uuid.UUID
    created_at: datetime.datetime


@dataclass(frozen=True)
class PersonFilmWork:
    target_table = "person_film_work"
    source_table = "person_film_work"

    id: uuid.UUID
    film_work_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    created_at: datetime.datetime
