from backend.database.connection import get_connection

def get_all_clients():
    """
    Obtiene todos los clientes registrados en la base de datos incluyendo su ubicacion (ciudad y estado).
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    id_cliente, 
                    nombre, 
                    telefono, 
                    rfc, 
                    correo, 
                    fecha_nacimiento, 
                    puntos_acumulados,
                    COALESCE(ciudad, 'N/A') AS ciudad,
                    COALESCE(estado, 'N/A') AS estado
                FROM Clientes
                ORDER BY id_cliente ASC;
            """
            cursor.execute(query)
            clients = cursor.fetchall()
            return clients
    except Exception as e:
        print(f"[Error al obtener clientes]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def create_client(nombre, telefono, rfc, correo, fecha_nacimiento, ciudad="Guadalajara", estado="Jalisco"):
    """
    Registra un nuevo cliente con consultas parametrizadas contra Inyeccion SQL,
    incluyendo ciudad y estado para el modulo de reportes.
    """
    nombre = (nombre or "").strip()
    telefono = (telefono or "").strip()
    rfc = (rfc or "").strip().upper()
    correo = (correo or "").strip()
    fecha_nacimiento = (fecha_nacimiento or None)
    ciudad = (ciudad or "").strip() or "Guadalajara"
    estado = (estado or "").strip() or "Jalisco"

    if not nombre or not telefono or not rfc:
        return False

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_cliente FROM Clientes WHERE UPPER(BTRIM(rfc)) = %s;",
                (rfc,)
            )
            if cursor.fetchone():
                print(f"[Error al registrar cliente]: El RFC '{rfc}' ya esta registrado.")
                return False

            query = """
                INSERT INTO Clientes (
                    nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados, ciudad, estado
                )
                VALUES (%s, %s, %s, %s, %s, 0, %s, %s);
            """
            cursor.execute(query, (nombre, telefono, rfc, correo, fecha_nacimiento, ciudad, estado))
            connection.commit()
            return True
    except Exception as e:
        print(f"[Error al registrar cliente]: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            connection.close()

def search_clients(search_term):
    """
    Busca clientes por coincidencia en nombre, RFC, correo electronico, ciudad o estado.
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    id_cliente, 
                    nombre, 
                    telefono, 
                    rfc, 
                    correo, 
                    fecha_nacimiento, 
                    puntos_acumulados,
                    COALESCE(ciudad, 'N/A') AS ciudad,
                    COALESCE(estado, 'N/A') AS estado
                FROM Clientes 
                WHERE nombre ILIKE %s 
                   OR rfc ILIKE %s 
                   OR correo ILIKE %s 
                   OR ciudad ILIKE %s 
                   OR estado ILIKE %s
                ORDER BY id_cliente ASC;
            """
            term_pattern = f"%{search_term.strip()}%"
            cursor.execute(query, (term_pattern, term_pattern, term_pattern, term_pattern, term_pattern))
            clients = cursor.fetchall()
            return clients
    except Exception as e:
        print(f"[Error al buscar clientes]: {e}")
        return []
    finally:
        if connection:
            connection.close()
