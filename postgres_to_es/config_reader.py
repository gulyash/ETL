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
    order_field: str
    state_field: str
    fetch_delay: Optional[float]
    state_file_path: Optional[str]
    sql_query_path: FilePath


class Elastic(BaseModel):
    index_name: str
    index_json_path: FilePath
    elastic_host: str


class Config(BaseModel):
    postgres: PostgresSettings
    elastic: Elastic


config = Config.parse_file("config.json")
