try:
    import psycopg
    from psycopg import pq
except Exception:
    import psycopg2 as psycopg

from backend.database.config import DB_CONFIG, DATABASE_URL

def get_connection():
    """
    Establece una conexion con PostgreSQL.
    Soporta DATABASE_URL directa o los parametros DB_CONFIG (con SSL para Supabase).
    Compatible tanto con psycopg (v3) como con psycopg2.
    """
    try:
        if DATABASE_URL:
            return psycopg.connect(DATABASE_URL)
        return psycopg.connect(**DB_CONFIG)
    except Exception as error:
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
    except Exception as error:
        print(f"No fue posible conectar: {error}")
