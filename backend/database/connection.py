
import psycopg
from backend.database.config import DB_CONFIG


def get_connection():
    """Establece una conexion con PostgreSQL."""

    try:
        connection = psycopg.connect(**DB_CONFIG)
        return connection

    except psycopg.Error as error:
        print(f"Error al conectar con PostgreSQL: {error}")
        raise


def test_connection():
    """Comprueba la conexion con PostgreSQL."""

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                result = cursor.fetchone()
                print("Conexion exitosa con PostgreSQL")
                print(result[0])

    except psycopg.Error as error:
        print(f"No fue posible conectar: {error}")
