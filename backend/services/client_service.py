from backend.database.connection import get_connection

def get_all_clients():
    """Obtiene todos los clientes registrados en la base de datos."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id_cliente, nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados FROM Clientes;")
        clients = cursor.fetchall()
        cursor.close()
        return clients
    except Exception as e:
        print(f"[Error al obtener clientes]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def create_client(nombre, telefono, rfc, correo, fecha_nacimiento):
    """Registra un nuevo cliente con consultas parametrizadas contra Inyección SQL."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = """
            INSERT INTO Clientes (nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados)
            VALUES (%s, %s, %s, %s, %s, 0);
        """
        cursor.execute(query, (nombre, telefono, rfc, correo, fecha_nacimiento))
        connection.commit()
        cursor.close()
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
    """Busca clientes por coincidencia en nombre, RFC o correo electrónico."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = """
            SELECT id_cliente, nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados 
            FROM Clientes 
            WHERE nombre ILIKE %s OR rfc ILIKE %s OR correo ILIKE %s;
        """
        term_pattern = f"%{search_term}%"
        cursor.execute(query, (term_pattern, term_pattern, term_pattern))
        clients = cursor.fetchall()
        cursor.close()
        return clients
    except Exception as e:
        print(f"[Error al buscar clientes]: {e}")
        return []
    finally:
        if connection:
            connection.close()