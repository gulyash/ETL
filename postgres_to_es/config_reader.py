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
    order_field: List[str]
    state_field: List[str]
    fetch_delay: Optional[float]
    state_file_path: Optional[str]
    sql_query_path: FilePath


class Elastic(BaseModel):
    index_json_path: FilePath
    elastic_host: str


class Config(BaseModel):
    postgres: PostgresSettings
    elastic: Elastic
