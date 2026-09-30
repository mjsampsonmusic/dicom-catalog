import os
from importlib import resources

import psycopg

DEFAULT_URL = "postgresql://dc:dc@localhost:5432/dicom_catalog"


def connect(url: str | None = None) -> psycopg.Connection:
    return psycopg.connect(url or os.environ.get("DATABASE_URL", DEFAULT_URL))


def init_schema(conn: psycopg.Connection) -> None:
    sql = resources.files("dicom_catalog").joinpath("schema.sql").read_text()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
