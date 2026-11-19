from datetime import datetime
from backend.database.connection import get_connection
from backend.models.client import Cliente
from backend.models.sale import Venta, DetalleVenta

def get_client_by_rfc(rfc: str):
    """
    Busca un cliente en la tabla Clientes a partir de su RFC.
    Retorna un diccionario con los datos del cliente o None si no existe.
    """
    if not rfc:
        return None

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
                WHERE LOWER(rfc) = LOWER(%s);
            """
            cursor.execute(query, (rfc.strip(),))
            rows = cursor.fetchall()
            if len(rows) > 1:
                raise ValueError(
                    f"Hay varios clientes registrados con el RFC '{rfc.strip()}'. "
                    "Corrija los duplicados antes de procesar la venta."
                )
            row = rows[0] if rows else None
            if row:
                return {
                    "id_cliente": row[0],
                    "nombre": row[1],
                    "telefono": row[2] or "",
                    "rfc": row[3],
                    "correo": row[4] or "",
                    "fecha_nacimiento": str(row[5]) if row[5] else "",
                    "puntos_acumulados": int(row[6]) if row[6] is not None else 0,
                    "ciudad": row[7],
                    "estado": row[8]
                }
            return None
    except ValueError:
        raise
    except Exception as e:
        print(f"[Error al consultar cliente por RFC]: {e}")
        return None
    finally:
        if connection:
            connection.close()

def validate_cart_restrictions(cart_items: list) -> tuple[bool, str]:
    """
    Regla de negocio critica de la farmacia:
    Comprueba si existe combinacion de medicamentos controlados (es_controlado=True)
    y productos alcoholicos (es_alcohol=True) en una misma compra.
    """
    if not cart_items:
        return False, "El carrito de compras esta vacio."

    tiene_controlado = any(item.get("es_controlado", False) for item in cart_items)
    tiene_alcohol = any(item.get("es_alcohol", False) for item in cart_items)

    if tiene_controlado and tiene_alcohol:
        return False, "Restriccion de venta: Esta estrictamente prohibido vender medicamentos controlados y bebidas alcoholicas en la misma compra."

    return True, "Carrito valido."

def calculate_sale_summary(cart_items: list, client_points: int) -> dict:
    """
    Calcula el desglose financiero de la venta y aplica el programa de lealtad:
    1. Subtotal base de los productos.
    2. Si el cliente tiene 50 puntos o mas: 10% de descuento y reseteo de puntos.
    3. Si el total supera los $500.00: asigna 10 puntos de lealtad.
    """
    subtotal = round(sum(item["cantidad"] * item["precio_unitario"] for item in cart_items), 2)
    
    # Evaluacion de lealtad: 50 puntos acumulados = 10% de descuento
    aplica_descuento = (int(client_points) >= 50)
    monto_descuento = round(subtotal * 0.10, 2) if aplica_descuento else 0.0
    total_con_descuento = round(subtotal - monto_descuento, 2)

    # Regla de lealtad: Compra mayor a $500.00 otorga 10 puntos
    puntos_ganados = 10 if total_con_descuento > 500.00 else 0

    return {
        "subtotal": subtotal,
        "aplica_descuento": aplica_descuento,
        "monto_descuento": monto_descuento,
        "total": total_con_descuento,
        "puntos_ganados": puntos_ganados,
        "puntos_a_resetear": aplica_descuento
    }

def process_sale(
    cart_items: list,
    id_cliente: int,
    id_usuario: int,
    metodo_pago: str = "Efectivo",
    efectivo_recibido: float = 0.0,
    requiere_factura: bool = False
) -> tuple[bool, str, int, dict]:
    """
    Ejecuta la transaccion completa de venta en la base de datos:
    1. Valida cliente obligatorio y restricciones de carrito.
    2. Comprueba stock disponible en tiempo real para cada producto.
    3. Inserta registro en la tabla Ventas y sus hijos en Detalle_Ventas.
    4. Resta el stock vendido de la tabla Productos.
    5. Actualiza los puntos acumulados del cliente segun el programa de lealtad.
    
    Retorna: (exito: bool, mensaje: str, id_venta: int, resumen: dict)
    """
    if not id_cliente:
        return False, "Es obligatorio asociar un cliente registrado a la venta.", None, {}

    if not cart_items:
        return False, "No hay productos en el carrito para procesar la venta.", None, {}

    # Validar restriccion alcohol + medicamento controlado
    es_valido, msg_restriccion = validate_cart_restrictions(cart_items)
    if not es_valido:
        return False, msg_restriccion, None, {}

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # 1. Asegurar usuario valido
            if not id_usuario:
                cursor.execute("SELECT id_usuario FROM Usuarios LIMIT 1;")
                row_u = cursor.fetchone()
                id_usuario = row_u[0] if row_u else 1

            # 2. Consultar cliente y puntos actuales
            cursor.execute("SELECT puntos_acumulados, nombre FROM Clientes WHERE id_cliente = %s;", (id_cliente,))
            cli_row = cursor.fetchone()
            if not cli_row:
                return False, f"El cliente con ID {id_cliente} no existe en la base de datos.", None, {}
            puntos_actuales = int(cli_row[0]) if cli_row[0] is not None else 0

            # 3. Comprobar stock disponible en PostgreSQL
            for item in cart_items:
                id_prod = item["id_producto"]
                cant_solicitada = int(item["cantidad"])

                cursor.execute("SELECT stock, nombre FROM Productos WHERE id_producto = %s;", (id_prod,))
                prod_row = cursor.fetchone()
                if not prod_row:
                    return False, f"El producto con ID {id_prod} no existe.", None, {}

                stock_disp, prod_nombre = prod_row
                stock_disp = int(stock_disp) if stock_disp is not None else 0
                if stock_disp < cant_solicitada:
                    return False, f"Stock insuficiente para '{prod_nombre}'. Disponible: {stock_disp}, Solicitado: {cant_solicitada}.", None, {}

            # 4. Calcular desglose y lealtad
            summary = calculate_sale_summary(cart_items, puntos_actuales)
            total = summary["total"]

            # 5. Validar metodo de pago y cambio
            if metodo_pago.lower() == "efectivo":
                efectivo_recibido = float(efectivo_recibido)
                if efectivo_recibido < total:
                    faltante = round(total - efectivo_recibido, 2)
                    return False, f"Monto en efectivo insuficiente. Total: ${total:.2f}, Recibido: ${efectivo_recibido:.2f} (Faltan: ${faltante:.2f}).", None, {}
                cambio_entregado = round(efectivo_recibido - total, 2)
            else:
                # Pago con Tarjeta
                efectivo_recibido = total
                cambio_entregado = 0.0

            # 6. Insertar registro en tabla Ventas
            query_venta = """
                INSERT INTO Ventas (
                    id_cliente, id_usuario, metodo_pago, efectivo_recibido, cambio_entregado, descuento_aplicado, total_venta
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_venta;
            """
            cursor.execute(query_venta, (
                id_cliente,
                id_usuario,
                metodo_pago,
                efectivo_recibido,
                cambio_entregado,
                summary["aplica_descuento"],
                total
            ))
            id_venta = cursor.fetchone()[0]

            # 7. Insertar en Detalle_Ventas y restar stock de Productos
            query_detalle = """
                INSERT INTO Detalle_Ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s);
            """
            query_restar_stock = """
                UPDATE Productos
                SET stock = stock - %s
                WHERE id_producto = %s;
            """
            for item in cart_items:
                cant = int(item["cantidad"])
                p_unit = float(item["precio_unitario"])
                subt = round(cant * p_unit, 2)

                cursor.execute(query_detalle, (id_venta, item["id_producto"], cant, p_unit, subt))
                cursor.execute(query_restar_stock, (cant, item["id_producto"]))

            # 8. Actualizar puntos del cliente
            if summary["puntos_a_resetear"]:
                nuevo_puntaje = 0 + summary["puntos_ganados"]
            else:
                nuevo_puntaje = puntos_actuales + summary["puntos_ganados"]

            cursor.execute("UPDATE Clientes SET puntos_acumulados = %s WHERE id_cliente = %s;", (nuevo_puntaje, id_cliente))

            connection.commit()

            summary["id_venta"] = id_venta
            summary["cambio_entregado"] = cambio_entregado
            summary["nuevo_puntaje"] = nuevo_puntaje

            msg = f"Venta #{id_venta} registrada exitosamente.\nTotal cobrado: ${total:,.2f} MXN."
            if cambio_entregado > 0:
                msg += f"\nCambio a entregar: ${cambio_entregado:,.2f} MXN."
            if summary["aplica_descuento"]:
                msg += "\nDescuento de lealtad del 10% aplicado y puntos canjeados."
            if summary["puntos_ganados"] > 0:
                msg += f"\nEl cliente acumulo +{summary['puntos_ganados']} puntos."

            return True, msg, id_venta, summary

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[Error en transaccion de venta]: {e}")
        return False, f"Error al procesar la venta en base de datos: {e}", None, {}
    finally:
        if connection:
            connection.close()

def get_recent_sales() -> list:
    """Retorna el historial reciente de ventas para consulta."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    v.id_venta,
                    c.nombre AS cliente_nombre,
                    u.nombre AS cajero_nombre,
                    v.fecha_hora,
                    v.metodo_pago,
                    v.descuento_aplicado,
                    v.total_venta
                FROM Ventas v
                LEFT JOIN Clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN Usuarios u ON v.id_usuario = u.id_usuario
                ORDER BY v.fecha_hora DESC
                LIMIT 50;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            sales = []
            for r in rows:
                sales.append({
                    "id_venta": r[0],
                    "cliente": r[1] or "Publico General",
                    "cajero": r[2] or "Cajero",
                    "fecha_hora": str(r[3]),
                    "metodo_pago": r[4],
                    "descuento_aplicado": bool(r[5]),
                    "total": float(r[6])
                })
            return sales
    except Exception as e:
        print(f"[Error al consultar ventas]: {e}")
        return []
    finally:
        if connection:
            connection.close()
