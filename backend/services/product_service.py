from backend.database.connection import get_connection
from backend.models.product import Producto

def get_all_products() -> list:
    """
    Obtiene todos los productos registrados en la base de datos junto con el nombre del proveedor.
    Retorna una lista de diccionarios.
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.id_producto, 
                    p.id_proveedor, 
                    p.folio, 
                    p.nombre, 
                    p.categoria, 
                    p.precio_compra, 
                    p.precio_venta, 
                    p.stock, 
                    p.es_controlado, 
                    p.es_alcohol,
                    pr.razon_social AS proveedor_nombre
                FROM Productos p
                LEFT JOIN Proveedores pr ON p.id_proveedor = pr.id_proveedor
                ORDER BY p.id_producto ASC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            products = []
            for row in rows:
                products.append({
                    "id_producto": row[0],
                    "id_proveedor": row[1],
                    "folio": row[2] or "S/F",
                    "nombre": row[3],
                    "categoria": row[4] or "General",
                    "precio_compra": float(row[5]),
                    "precio_venta": float(row[6]),
                    "stock": int(row[7]) if row[7] is not None else 0,
                    "es_controlado": bool(row[8]) if row[8] is not None else False,
                    "es_alcohol": bool(row[9]) if row[9] is not None else False,
                    "proveedor_nombre": row[10] or "Sin Proveedor"
                })
            return products
    except Exception as e:
        print(f"[Error al obtener productos]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def search_products(search_term: str) -> list:
    """
    Busca productos por coincidencia en nombre, folio o categoria.
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.id_producto, 
                    p.id_proveedor, 
                    p.folio, 
                    p.nombre, 
                    p.categoria, 
                    p.precio_compra, 
                    p.precio_venta, 
                    p.stock, 
                    p.es_controlado, 
                    p.es_alcohol,
                    pr.razon_social AS proveedor_nombre
                FROM Productos p
                LEFT JOIN Proveedores pr ON p.id_proveedor = pr.id_proveedor
                WHERE p.nombre ILIKE %s OR p.folio ILIKE %s OR p.categoria ILIKE %s
                ORDER BY p.id_producto ASC;
            """
            pattern = f"%{search_term.strip()}%"
            cursor.execute(query, (pattern, pattern, pattern))
            rows = cursor.fetchall()
            products = []
            for row in rows:
                products.append({
                    "id_producto": row[0],
                    "id_proveedor": row[1],
                    "folio": row[2] or "S/F",
                    "nombre": row[3],
                    "categoria": row[4] or "General",
                    "precio_compra": float(row[5]),
                    "precio_venta": float(row[6]),
                    "stock": int(row[7]) if row[7] is not None else 0,
                    "es_controlado": bool(row[8]) if row[8] is not None else False,
                    "es_alcohol": bool(row[9]) if row[9] is not None else False,
                    "proveedor_nombre": row[10] or "Sin Proveedor"
                })
            return products
    except Exception as e:
        print(f"[Error al buscar productos]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def get_product_by_id(id_producto: int):
    """Consulta un producto individual por su ID primario."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT id_producto, id_proveedor, folio, nombre, categoria, precio_compra, precio_venta, stock, es_controlado, es_alcohol
                FROM Productos
                WHERE id_producto = %s;
            """
            cursor.execute(query, (id_producto,))
            row = cursor.fetchone()
            if row:
                return Producto.from_row(row)
            return None
    except Exception as e:
        print(f"[Error al consultar producto por ID]: {e}")
        return None
    finally:
        if connection:
            connection.close()

def get_product_by_folio(folio: str):
    """Consulta un producto individual por su folio unico."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT id_producto, id_proveedor, folio, nombre, categoria, precio_compra, precio_venta, stock, es_controlado, es_alcohol
                FROM Productos
                WHERE LOWER(folio) = LOWER(%s);
            """
            cursor.execute(query, (folio.strip(),))
            row = cursor.fetchone()
            if row:
                return Producto.from_row(row)
            return None
    except Exception as e:
        print(f"[Error al consultar producto por folio]: {e}")
        return None
    finally:
        if connection:
            connection.close()

def generate_default_folio(categoria: str, cursor) -> str:
    """Genera un folio estructurado consecutivo basado en la categoria."""
    cat_upper = (categoria or "GEN").upper().strip()
    prefix = cat_upper[:3] if len(cat_upper) >= 3 else cat_upper.ljust(3, "X")

    cursor.execute(
        "SELECT folio FROM Productos WHERE UPPER(LEFT(folio, %s)) = %s;",
        (len(prefix), prefix)
    )
    existing_folios = cursor.fetchall()
    max_number = 0
    for (existing_folio,) in existing_folios:
        suffix = existing_folio[len(prefix):]
        if suffix.startswith("-") and suffix[1:].isdigit():
            max_number = max(max_number, int(suffix[1:]))
    return f"{prefix}-{max_number + 1:03d}"

def get_providers_list() -> list:
    """Retorna una lista de proveedores (id_proveedor, razon_social) para llenar listas desplegables."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_proveedor, razon_social FROM Proveedores ORDER BY razon_social ASC;")
            return cursor.fetchall()
    except Exception as e:
        print(f"[Error al obtener proveedores]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def create_product(
    nombre: str,
    categoria: str,
    precio_compra: float,
    precio_venta: float,
    stock: int = 0,
    es_controlado: bool = False,
    es_alcohol: bool = False,
    id_proveedor: int = None,
    folio: str = None,
    creator_role: str = "Admin"
) -> tuple[bool, str]:
    """
    Registra un nuevo producto aplicando las reglas de negocio del sistema:
    1. Restriccion de roles: Solo Admin y Gerente pueden registrar productos.
    2. Validacion de datos numericos y obligatorios.
    3. Asignacion o verificacion de folio unico.
    4. Control de banderas es_controlado y es_alcohol.
    
    Retorna: (exito: bool, mensaje: str)
    """
    if creator_role not in ["Admin", "Gerente"]:
        return False, "Permiso denegado: Solo el Administrador y el Gerente pueden registrar productos."

    nombre = (nombre or "").strip()
    categoria = (categoria or "").strip()

    if not nombre:
        return False, "El nombre del producto es obligatorio."

    try:
        precio_compra = float(precio_compra)
        precio_venta = float(precio_venta)
        stock = int(stock)
    except (ValueError, TypeError):
        return False, "Los precios y el stock deben ser valores numericos validos."

    if precio_compra < 0 or precio_venta < 0:
        return False, "Los precios no pueden ser negativos."

    if stock < 0:
        return False, "El stock inicial no puede ser negativo."

    if id_proveedor is None:
        return False, "Debe seleccionar un proveedor para el producto."

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Generar folio si no fue proporcionado
            if not folio or not folio.strip():
                folio = generate_default_folio(categoria, cursor)
            else:
                folio = folio.strip()

            cursor.execute("SELECT id_producto FROM Productos WHERE LOWER(folio) = LOWER(%s);", (folio,))
            if cursor.fetchone():
                return False, f"El folio '{folio}' ya pertenece a otro producto registrado."

            cursor.execute("SELECT id_proveedor FROM Proveedores WHERE id_proveedor = %s;", (id_proveedor,))
            if not cursor.fetchone():
                return False, "El proveedor seleccionado no existe."

            query = """
                INSERT INTO Productos (
                    id_proveedor, folio, nombre, categoria, precio_compra, precio_venta, stock, es_controlado, es_alcohol
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_producto;
            """
            cursor.execute(query, (
                id_proveedor,
                folio,
                nombre,
                categoria,
                precio_compra,
                precio_venta,
                stock,
                bool(es_controlado),
                bool(es_alcohol)
            ))
            nuevo_id = cursor.fetchone()[0]
            connection.commit()

            return True, f"Producto '{nombre}' registrado exitosamente con Folio: {folio} (ID: {nuevo_id})."

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[Error al registrar producto]: {e}")
        return False, f"Error en la base de datos: {e}"
    finally:
        if connection:
            connection.close()

def assign_product_provider(
    id_producto: int,
    id_proveedor: int,
    creator_role: str = "Admin"
) -> tuple[bool, str]:
    """Asigna un proveedor a un producto existente."""
    if creator_role not in ["Admin", "Gerente"]:
        return False, "Permiso denegado: Solo el Administrador y el Gerente pueden modificar productos."

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_producto FROM Productos WHERE id_producto = %s;", (id_producto,))
            if not cursor.fetchone():
                return False, "El producto seleccionado ya no existe."

            cursor.execute("SELECT id_proveedor FROM Proveedores WHERE id_proveedor = %s;", (id_proveedor,))
            if not cursor.fetchone():
                return False, "El proveedor seleccionado no existe."

            cursor.execute(
                "UPDATE Productos SET id_proveedor = %s WHERE id_producto = %s;",
                (id_proveedor, id_producto)
            )
            connection.commit()
            return True, "Proveedor asignado correctamente al producto."
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[Error al asignar proveedor al producto {id_producto}]: {e}")
        return False, f"Error al asignar proveedor: {e}"
    finally:
        if connection:
            connection.close()

def update_product(
    id_producto: int,
    nombre: str,
    categoria: str,
    precio_compra: float,
    precio_venta: float,
    stock: int,
    es_controlado: bool,
    es_alcohol: bool,
    id_proveedor: int = None,
    folio: str = None,
    creator_role: str = "Admin"
) -> tuple[bool, str]:
    """Actualiza la informacion de un producto existente."""
    if creator_role not in ["Admin", "Gerente"]:
        return False, "Permiso denegado: Solo el Administrador y el Gerente pueden modificar productos."

    nombre = (nombre or "").strip()
    if not nombre:
        return False, "El nombre del producto no puede estar vacio."

    try:
        precio_compra = float(precio_compra)
        precio_venta = float(precio_venta)
        stock = int(stock)
    except (ValueError, TypeError):
        return False, "Los precios y el stock deben ser numericos."

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Validar existencia
            cursor.execute("SELECT id_producto FROM Productos WHERE id_producto = %s;", (id_producto,))
            if not cursor.fetchone():
                return False, "El producto a modificar no existe."

            # Validar folio unico en otros productos
            if folio:
                folio = folio.strip()
                cursor.execute(
                    "SELECT id_producto FROM Productos WHERE LOWER(folio) = LOWER(%s) AND id_producto != %s;",
                    (folio, id_producto)
                )
                if cursor.fetchone():
                    return False, f"El folio '{folio}' ya esta siendo utilizado por otro producto."

            query = """
                UPDATE Productos
                SET nombre = %s,
                    categoria = %s,
                    precio_compra = %s,
                    precio_venta = %s,
                    stock = %s,
                    es_controlado = %s,
                    es_alcohol = %s,
                    id_proveedor = %s,
                    folio = COALESCE(%s, folio)
                WHERE id_producto = %s;
            """
            cursor.execute(query, (
                nombre,
                categoria,
                precio_compra,
                precio_venta,
                stock,
                bool(es_controlado),
                bool(es_alcohol),
                id_proveedor,
                folio,
                id_producto
            ))
            connection.commit()
            return True, f"Producto '{nombre}' actualizado correctamente."

    except Exception as e:
        if connection:
            connection.rollback()
        return False, f"Error al actualizar producto: {e}"
    finally:
        if connection:
            connection.close()

def delete_product(id_producto: int, creator_role: str = "Admin") -> tuple[bool, str]:
    """Elimina un producto del catalogo respetando permisos."""
    if creator_role not in ["Admin", "Gerente"]:
        return False, "Permiso denegado: Solo el Administrador y el Gerente pueden eliminar productos."

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT nombre FROM Productos WHERE id_producto = %s;", (id_producto,))
            prod = cursor.fetchone()
            if not prod:
                return False, "El producto a eliminar no existe."

            cursor.execute("DELETE FROM Productos WHERE id_producto = %s;", (id_producto,))
            connection.commit()
            return True, f"Producto '{prod[0]}' eliminado del catalogo."

    except Exception as e:
        if connection:
            connection.rollback()
        return False, f"No se puede eliminar el producto (posiblemente vinculado a ventas o compras): {e}"
    finally:
        if connection:
            connection.close()
