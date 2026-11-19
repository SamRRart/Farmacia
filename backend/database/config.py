import os
from dotenv import load_dotenv

# Cargar configuracion local desde .env
load_dotenv()

# Configuracion centralizada de PostgreSQL (compatible con local y Supabase/Cloud)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "sslmode": os.getenv("DB_SSLMODE", "prefer")
}

DATABASE_URL = os.getenv("DATABASE_URL")
