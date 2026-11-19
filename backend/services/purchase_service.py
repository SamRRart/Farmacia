from datetime import datetime
from backend.database.connection import get_connection
from backend.models.purchase import Compra, DetalleCompra

def get_pending_purchases() -> list:
    """
    Obtiene todas las ordenes de compra en estado 'Enviado' pendientes de recepcion fisica.
    Retorna una lista de diccionarios con datos del proveedor y usuario solicitante.
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    c.id_compra, 
                    c.id_proveedor, 
                    pr.razon_social AS proveedor_nombre,
                    c.id_usuario, 
                    u.nombre AS usuario_nombre,
                    c.fecha_hora, 
                    c.estado_pedido, 
                    c.total_compra
                FROM Compras c
                LEFT JOIN Proveedores pr ON c.id_proveedor = pr.id_proveedor
                LEFT JOIN Usuarios u ON c.id_usuario = u.id_usuario
                WHERE c.estado_pedido = 'Enviado'
                ORDER BY c.fecha_hora DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            purchases = []
            for r in rows:
                purchases.append({
                    "id_compra": r[0],
                    "id_proveedor": r[1],
                    "proveedor_nombre": r[2] or "Proveedor Desconocido",
                    "id_usuario": r[3],
                    "usuario_nombre": r[4] or "Usuario Desconocido",
                    "fecha_hora": str(r[5]),
                    "estado_pedido": r[6],
                    "total_compra": float(r[7])
                })
            return purchases
    except Exception as e:
        print(f"[Error al obtener compras pendientes]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def get_all_purchases_history() -> list:
    """
    Obtiene el historial completo de compras (Enviado, Surtido, etc.).
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    c.id_compra, 
                    pr.razon_social AS proveedor_nombre,
                    u.nombre AS usuario_nombre,
                    c.fecha_hora, 
                    c.estado_pedido, 
                    c.total_compra
                FROM Compras c
                LEFT JOIN Proveedores pr ON c.id_proveedor = pr.id_proveedor
                LEFT JOIN Usuarios u ON c.id_usuario = u.id_usuario
                ORDER BY c.fecha_hora DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            history = []
            for r in rows:
                history.append({
                    "id_compra": r[0],
                    "proveedor_nombre": r[1] or "Proveedor Desconocido",
                    "usuario_nombre": r[2] or "Usuario Desconocido",
                    "fecha_hora": str(r[3]),
                    "estado_pedido": r[4],
                    "total_compra": float(r[5])
                })
            return history
    except Exception as e:
        print(f"[Error al consultar historial de compras]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def get_purchase_details(id_compra: int) -> list:
    """
    Obtiene el desglose de productos asociados a una orden de compra especifica.
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    dc.id_detalle_compra,
                    dc.id_producto,
                    p.nombre AS producto_nombre,
                    p.folio AS producto_folio,
                    dc.cantidad,
                    dc.precio_compra_unitario,
                    dc.subtotal,
                    p.precio_venta AS precio_venta_actual,
                    p.stock AS stock_actual
                FROM Detalle_Compras dc
                JOIN Productos p ON dc.id_producto = p.id_producto
                WHERE dc.id_compra = %s
                ORDER BY dc.id_detalle_compra ASC;
            """
            cursor.execute(query, (id_compra,))
            rows = cursor.fetchall()
            details = []
            for r in rows:
                details.append({
                    "id_detalle_compra": r[0],
                    "id_producto": r[1],
                    "producto_nombre": r[2],
                    "producto_folio": r[3] or "S/F",
                    "cantidad": int(r[4]),
                    "precio_compra_unitario": float(r[5]),
                    "subtotal": float(r[6]),
                    "precio_venta_actual": float(r[7]),
                    "stock_actual": int(r[8]) if r[8] is not None else 0
                })
            return details
    except Exception as e:
        print(f"[Error al consultar detalle de compra {id_compra}]: {e}")
        return []
    finally:
        if connection:
            connection.close()

def get_purchase_notification_data(id_compra: int) -> tuple[bool, str, dict]:
    """Obtiene el proveedor y el detalle necesarios para notificar una orden."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.razon_social, p.correo, c.total_compra
                FROM Compras c
                JOIN Proveedores p ON c.id_proveedor = p.id_proveedor
                WHERE c.id_compra = %s;
            """, (id_compra,))
            purchase = cursor.fetchone()
            if not purchase:
                return False, f"No se encontraron los datos del proveedor para la orden #{id_compra}.", {}

            cursor.execute("""
                SELECT p.nombre, dc.cantidad, dc.precio_compra_unitario, dc.subtotal
                FROM Detalle_Compras dc
                JOIN Productos p ON dc.id_producto = p.id_producto
                WHERE dc.id_compra = %s
                ORDER BY dc.id_detalle_compra ASC;
            """, (id_compra,))
            rows = cursor.fetchall()
            if not rows:
                return False, f"La orden #{id_compra} no tiene productos para notificar.", {}

            return True, "", {
                "provider_email": purchase[1] or "",
                "provider_name": purchase[0],
                "order_id": id_compra,
                "items_list": [
                    {
                        "nombre": row[0],
                        "cantidad": row[1],
                        "precio_compra_unitario": float(row[2]),
                        "subtotal": float(row[3])
                    }
                    for row in rows
                ],
                "total_amount": float(purchase[2] or 0)
            }
    except Exception as e:
        print(f"[Error al preparar notificacion de compra #{id_compra}]: {e}")
        return False, f"No se pudo preparar el correo de la orden #{id_compra}: {e}", {}
    finally:
        if connection:
            connection.close()

def create_restock_orders(items_list: list, id_usuario: int, creator_role: str = "Gerente") -> tuple[bool, str, list]:
    """
    Procesa la solicitud de reabastecimiento (Restock):
    1. Agrupa automaticamente los productos seleccionados por su proveedor (id_proveedor).
    2. Por cada proveedor, genera una orden independiente en la tabla Compras (estado_pedido='Enviado').
    3. Registra cada producto en Detalle_Compras.
    4. NO modifica el stock todavia (espera recepcion fisica).
    
    Retorna: (exito: bool, mensaje: str, lista_id_compras_generadas: list)
    """
    if creator_role not in ["Admin", "Gerente"]:
        return False, "Permiso denegado: Solo el Administrador o Gerente pueden solicitar restock.", []

    if not items_list:
        return False, "La lista de productos para restock esta vacia.", []

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # 1. Asegurar id_usuario valido
            if not id_usuario:
                cursor.execute("SELECT id_usuario FROM Usuarios WHERE perfil IN ('Admin', 'Gerente') LIMIT 1;")
                row_user = cursor.fetchone()
                id_usuario = row_user[0] if row_user else None

            if not id_usuario:
                return False, "No se encontro un usuario valido para asociar la compra.", []

            # 2. Obtener datos completos de cada producto y agrupar por id_proveedor
            grouped_by_provider = {}
            for item in items_list:
                id_prod = item.get("id_producto")
                try:
                    cant = int(item.get("cantidad", 1))
                except (TypeError, ValueError):
                    return False, "La cantidad de cada producto debe ser un entero positivo.", []
                if cant <= 0:
                    return False, "La cantidad de cada producto debe ser un entero positivo.", []

                cursor.execute("SELECT id_producto, id_proveedor, nombre, precio_compra FROM Productos WHERE id_producto = %s;", (id_prod,))
                prod_row = cursor.fetchone()
                if not prod_row:
                    return False, f"El producto con ID {id_prod} ya no existe en el catalogo.", []

                prod_id, id_prov, prod_nombre, db_p_compra = prod_row
                p_compra = float(item.get("precio_compra_unitario", db_p_compra))
                subtotal = round(cant * p_compra, 2)

                if not id_prov:
                    return False, (
                        f"El producto '{prod_nombre}' no tiene proveedor asignado. "
                        "Asigne un proveedor al producto antes de solicitar el restock."
                    ), []

                if id_prov not in grouped_by_provider:
                    grouped_by_provider[id_prov] = []

                grouped_by_provider[id_prov].append({
                    "id_producto": prod_id,
                    "nombre": prod_nombre,
                    "cantidad": cant,
                    "precio_compra_unitario": p_compra,
                    "subtotal": subtotal
                })

            if not grouped_by_provider:
                return False, "No hay productos validos para generar ordenes de compra.", []

            # 3. Insertar compras independientes por cada proveedor
            created_purchases = []
            for id_prov, prods in grouped_by_provider.items():
                total_orden = round(sum(p["subtotal"] for p in prods), 2)

                # Insertar cabecera de Compra
                query_compra = """
                    INSERT INTO Compras (id_proveedor, id_usuario, estado_pedido, total_compra)
                    VALUES (%s, %s, 'Enviado', %s)
                    RETURNING id_compra;
                """
                cursor.execute(query_compra, (id_prov, id_usuario, total_orden))
                id_compra = cursor.fetchone()[0]
                created_purchases.append(id_compra)

                # Insertar detalles de la Compra
                query_detalle = """
                    INSERT INTO Detalle_Compras (id_compra, id_producto, cantidad, precio_compra_unitario, subtotal)
                    VALUES (%s, %s, %s, %s, %s);
                """
                for p in prods:
                    cursor.execute(query_detalle, (
                        id_compra,
                        p["id_producto"],
                        p["cantidad"],
                        p["precio_compra_unitario"],
                        p["subtotal"]
                    ))

            connection.commit()
            msg = f"Restock generado con exito. Se crearon {len(created_purchases)} ordenes de compra agrupadas por proveedor con estado 'Enviado'."
            return True, msg, created_purchases

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[Error al crear ordenes de compra]: {e}")
        return False, f"Error en base de datos: {e}", []
    finally:
        if connection:
            connection.close()

def receive_purchase(
    id_compra: int,
    price_updates: dict = None,
    creator_role: str = "Gerente"
) -> tuple[bool, str]:
    """
    Marca una orden de compra como recibida físicamente:
    1. Cambia estado_pedido a 'Surtido'.
    2. Suma las cantidades recibidas al stock actual de cada producto en la tabla Productos.
    3. Si se especifican nuevos precios (price_updates), actualiza precio_compra y precio_venta en Productos.
    
    price_updates: {id_producto: {"precio_compra": float, "precio_venta": float}} (opcional)
    Retorna: (exito: bool, mensaje: str)
    """
    if creator_role not in ["Admin", "Gerente"]:
        return False, "Permiso denegado: Solo el Administrador o Gerente pueden marcar compras como recibidas."

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # 1. Verificar estado actual de la compra
            cursor.execute("SELECT estado_pedido FROM Compras WHERE id_compra = %s;", (id_compra,))
            compra_row = cursor.fetchone()
            if not compra_row:
                return False, f"La orden de compra ID {id_compra} no existe."

            if compra_row[0] == "Surtido":
                return False, f"La orden de compra ID {id_compra} ya habia sido marcada como 'Surtido' previamente."

            # 2. Consultar productos y cantidades para sumar al stock
            cursor.execute("SELECT id_producto, cantidad, precio_compra_unitario FROM Detalle_Compras WHERE id_compra = %s;", (id_compra,))
            items = cursor.fetchall()

            for id_prod, cant, p_compra_unit in items:
                # Actualizar stock
                cursor.execute("""
                    UPDATE Productos
                    SET stock = stock + %s
                    WHERE id_producto = %s;
                """, (cant, id_prod))

                # Actualizar precios si se indicaron
                if price_updates and id_prod in price_updates:
                    p_info = price_updates[id_prod]
                    new_pc = p_info.get("precio_compra")
                    new_pv = p_info.get("precio_venta")
                    if new_pc is not None and new_pv is not None:
                        cursor.execute("""
                            UPDATE Productos
                            SET precio_compra = %s, precio_venta = %s
                            WHERE id_producto = %s;
                        """, (new_pc, new_pv, id_prod))
                    elif new_pc is not None:
                        cursor.execute("""
                            UPDATE Productos
                            SET precio_compra = %s
                            WHERE id_producto = %s;
                        """, (new_pc, id_prod))

            # 3. Cambiar estado de la compra a 'Surtido'
            cursor.execute("UPDATE Compras SET estado_pedido = 'Surtido' WHERE id_compra = %s;", (id_compra,))

            connection.commit()
            return True, f"Orden de compra #{id_compra} marcada como 'Surtido'. El inventario y stock han sido actualizados correctamente."

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[Error al recibir orden de compra]: {e}")
        return False, f"Error al procesar la recepcion de la compra: {e}"
    finally:
        if connection:
            connection.close()
