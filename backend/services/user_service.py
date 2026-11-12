import bcrypt
from backend.database.connection import get_connection

def hash_password(plain_password):
    """Genera un hash seguro de la contraseña para guardarla al registrar usuarios."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def authenticate_db_user(username_or_email, password):
    """
    Verifica las credenciales del usuario en la tabla `Usuarios` usando hashes bcrypt.
    Respeta la columna original 'perfil' de la base de datos.
    Retorna el perfil del usuario si es válido, o None si falla.
    """
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Consulta 100% segura contra Inyección SQL utilizando parámetros (%s)
        # Seleccionamos 'perfil' tal como está definido en la estructura original de la BD
        query = """
            SELECT perfil, password FROM Usuarios 
            WHERE correo = %s OR nombre = %s;
        """
        cursor.execute(query, (username_or_email, username_or_email))
        result = cursor.fetchone()
        cursor.close()

        if result:
            db_perfil, db_hashed_password = result
            
            # Verificación segura de la contraseña mediante bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), db_hashed_password.encode('utf-8')):
                return db_perfil
                
        return None

    except Exception as e:
        print(f"[Error en autenticación segura]: {e}")
        return None
    finally:
        if connection:
            connection.close()