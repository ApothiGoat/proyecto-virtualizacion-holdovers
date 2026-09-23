import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    """Abre una conexión nueva a Postgres usando variables de entorno.

    Cada microservicio tiene su propia base de datos y su propio usuario,
    tal como pide el enunciado (sin secretos quemados en el código).
    """
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        cursor_factory=RealDictCursor,
    )
