import bcrypt
import re
from backend.database.connection import get_connection
from backend.models.user import Usuario

def hash_password(plain_password: str) -> str:
    """Genera un hash seguro de la contraseña para guardarla al registrar usuarios."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba si la contraseña en texto plano coincide con el hash almacenado."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"[Error al verificar contraseña]: {e}")
        return False

def authenticate_db_user(username_or_email: str, password: str):
    """
    Verifica las credenciales del usuario en la tabla `Usuarios` usando hashes bcrypt.
    Retorna un diccionario con los datos del usuario si es válido, o None si falla.
    """
    if not username_or_email or not password:
        return None

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT id_usuario, perfil, nombre, correo, password 
                FROM Usuarios 
                WHERE LOWER(correo) = LOWER(%s) OR LOWER(nombre) = LOWER(%s);
            """
            cursor.execute(query, (username_or_email.strip(), username_or_email.strip()))
            result = cursor.fetchone()

            if result:
                id_usuario, perfil, nombre, correo, db_hashed_password = result
                if check_password(password, db_hashed_password):
                    return {
                        "id_usuario": id_usuario,
                        "perfil": perfil,
                        "nombre": nombre,
                        "correo": correo
                    }
        return None

    except Exception as e:
        print(f"[Error en autenticación segura]: {e}")
        return None
    finally:
        if connection:
            connection.close()

def count_admins(cursor=None) -> int:
    """Retorna la cantidad actual de usuarios con perfil Admin en el sistema."""
    should_close = False
    connection = None
    try:
        if cursor is None:
            connection = get_connection()
            cursor = connection.cursor()
            should_close = True

        cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE LOWER(perfil) = 'admin';")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"[Error al contar administradores]: {e}")
        return 0
    finally:
        if should_close:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

def get_all_users() -> list:
    """
    Obtiene todos los usuarios registrados en la base de datos (sin exponer el hash de contraseña).
    Retorna una lista de diccionarios.
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT id_usuario, perfil, nombre, correo 
                FROM Usuarios 
                ORDER BY id_usuario ASC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append({
                    "id_usuario": row[0],
                    "perfil": row[1],
                    "nombre": row[2],
                    "correo": row[3]
                })
            return users
    except Exception as e:
        print(f"[Error al obtener usuarios]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def create_user(nombre: str, correo: str, password: str, perfil: str, creator_role: str = "Admin") -> tuple[bool, str]:
    """
    Registra un nuevo usuario aplicando las reglas de negocio estrictas:
    1. Campos obligatorios y formato de correo.
    2. Restricción crítica: Solo puede existir 1 Admin en todo el sistema.
    3. Restricción de permisos: El Gerente solo puede dar de alta a usuarios con perfil 'Encargado'.
    4. El correo debe ser único.
    5. Contraseña almacenada con hash bcrypt.
    
    Retorna: (éxito: bool, mensaje: str)
    """
    nombre = (nombre or "").strip()
    correo = (correo or "").strip()
    password = (password or "").strip()
    perfil = (perfil or "").strip()

    # Validaciones básicas de entrada
    if not nombre or not correo or not password or not perfil:
        return False, "Todos los campos (Nombre, Correo, Contraseña y Perfil) son obligatorios."

    if len(password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", correo):
        return False, "El formato del correo electrónico no es válido."

    perfiles_validos = ["Admin", "Gerente", "Encargado"]
    if perfil not in perfiles_validos:
        return False, f"Perfil inválido. Debe ser uno de: {', '.join(perfiles_validos)}."

    # Regla de permisos: Gerente solo puede crear Encargados
    if creator_role == "Gerente" and perfil != "Encargado":
        return False, "Permiso denegado: El Gerente únicamente tiene autorización para dar de alta Encargados."

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # 1. Validar que el correo no esté repetido
            cursor.execute("SELECT id_usuario FROM Usuarios WHERE LOWER(correo) = LOWER(%s);", (correo,))
            if cursor.fetchone():
                return False, f"El correo '{correo}' ya se encuentra registrado por otro usuario."

            # 2. Restricción crítica: Máximo 1 Admin en todo el sistema
            if perfil == "Admin":
                num_admins = count_admins(cursor)
                if num_admins >= 1:
                    return False, "Restricción del sistema: Solo puede existir 1 Administrador en el sistema."

            # 3. Hasheo seguro de la contraseña
            hashed_pw = hash_password(password)

            # 4. Inserción con parámetros seguros contra SQL Injection
            query = """
                INSERT INTO Usuarios (perfil, nombre, correo, password)
                VALUES (%s, %s, %s, %s)
                RETURNING id_usuario;
            """
            cursor.execute(query, (perfil, nombre, correo, hashed_pw))
            nuevo_id = cursor.fetchone()[0]
            connection.commit()

            return True, f"Usuario '{nombre}' registrado exitosamente con ID {nuevo_id} (Perfil: {perfil})."

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[Error al crear usuario]: {e}")
        return False, f"Error en la base de datos: {e}"
    finally:
        if connection:
            connection.close()

def delete_user(id_usuario: int, creator_role: str = "Admin") -> tuple[bool, str]:
    """Elimina un usuario respetando permisos (Solo Admin puede eliminar usuarios)."""
    if creator_role != "Admin":
        return False, "Permiso denegado: Solo el Administrador puede eliminar usuarios."

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Verificar si existe y su rol
            cursor.execute("SELECT perfil, nombre FROM Usuarios WHERE id_usuario = %s;", (id_usuario,))
            user = cursor.fetchone()
            if not user:
                return False, "El usuario a eliminar no existe."

            if user[0].lower() == "admin":
                cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE LOWER(perfil) = 'admin';")
                if cursor.fetchone()[0] <= 1:
                    return False, "No se puede eliminar al unico administrador del sistema."

            cursor.execute("DELETE FROM Usuarios WHERE id_usuario = %s;", (id_usuario,))
            connection.commit()
            return True, f"Usuario '{user[1]}' eliminado correctamente."
    except Exception as e:
        if connection:
            connection.rollback()
        return False, f"Error al eliminar usuario: {e}"
    finally:
        if connection:
            connection.close()
