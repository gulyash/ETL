from typing import Optional, List
from pydantic import BaseModel, FilePath


class DSNSettings(BaseModel):
    host: str
    port: int
    dbname: str
    password: str
    user: str


class PostgresSettings(BaseModel):
    dsn: DSNSettings
    limit: Optional[int]
    fetch_delay: Optional[float]


class Elastic(BaseModel):
    index_name: str
    index_json_path: FilePath
    elastic_host: str


class StateSettings(BaseModel):
    file_path: Optional[str]


class Config(BaseModel):
    postgres: PostgresSettings
    elastic: Elastic
    state: StateSettings


config = Config.parse_file("config.json")
