from datetime import datetime

class DetalleVenta:
    """
    Representa una linea de producto dentro de una transaccion de venta.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(
        self,
        id_detalle_venta=None,
        id_venta=None,
        id_producto=None,
        cantidad=1,
        precio_unitario=0.0,
        subtotal=0.0,
        producto_nombre="",
        producto_folio="",
        es_controlado=False,
        es_alcohol=False
    ):
        self.id_detalle_venta = id_detalle_venta
        self.id_venta = id_venta
        self.id_producto = id_producto
        self.cantidad = int(cantidad)
        self.precio_unitario = float(precio_unitario)
        self.subtotal = float(subtotal) if subtotal else self.calcular_subtotal()
        self.producto_nombre = producto_nombre
        self.producto_folio = producto_folio
        self.es_controlado = bool(es_controlado)
        self.es_alcohol = bool(es_alcohol)

    def calcular_subtotal(self) -> float:
        self.subtotal = round(self.cantidad * self.precio_unitario, 2)
        return self.subtotal

    def to_dict(self) -> dict:
        return {
            "id_detalle_venta": self.id_detalle_venta,
            "id_venta": self.id_venta,
            "id_producto": self.id_producto,
            "producto_nombre": self.producto_nombre,
            "producto_folio": self.producto_folio,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal,
            "es_controlado": self.es_controlado,
            "es_alcohol": self.es_alcohol
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id_detalle_venta, id_venta, id_producto, cantidad, precio_unitario, subtotal)
        return cls(
            id_detalle_venta=row[0],
            id_venta=row[1],
            id_producto=row[2],
            cantidad=row[3],
            precio_unitario=row[4],
            subtotal=row[5]
        )

    def __repr__(self):
        return f"<DetalleVenta Prod:{self.id_producto} Cant:{self.cantidad} Subtotal:${self.subtotal}>"


class Venta:
    """
    Representa una venta comercial en la farmacia.
    Contiene la validacion de restricciones de carrito, calculo de totales,
    evaluacion del descuento de lealtad y registro de metodos de pago.
    """
    def __init__(
        self,
        id_venta=None,
        id_cliente=None,
        id_usuario=None,
        fecha_hora=None,
        metodo_pago="Efectivo",
        efectivo_recibido=0.0,
        cambio_entregado=0.0,
        descuento_aplicado=False,
        total_venta=0.0,
        detalles=None
    ):
        self.id_venta = id_venta
        self.id_cliente = id_cliente
        self.id_usuario = id_usuario
        self.fecha_hora = fecha_hora or datetime.now()
        self.metodo_pago = metodo_pago
        self.efectivo_recibido = float(efectivo_recibido)
        self.cambio_entregado = float(cambio_entregado)
        self.descuento_aplicado = bool(descuento_aplicado)
        self.total_venta = float(total_venta)
        self.detalles = detalles if detalles is not None else []

    def agregar_detalle(self, detalle: DetalleVenta) -> None:
        self.detalles.append(detalle)
        self.calcular_total()

    def calcular_subtotal_base(self) -> float:
        return round(sum(d.calcular_subtotal() for d in self.detalles), 2)

    def calcular_total(self) -> float:
        subtotal = self.calcular_subtotal_base()
        if self.descuento_aplicado:
            descuento = round(subtotal * 0.10, 2)
            self.total_venta = round(subtotal - descuento, 2)
        else:
            self.total_venta = subtotal
        return self.total_venta

    def validar_restricciones_carrito(self) -> tuple[bool, str]:
        """
        Regla de negocio critica: Esta estrictamente prohibido vender
        medicamentos controlados (es_controlado=True) y bebidas alcoholicas
        (es_alcohol=True) en una misma transaccion.
        """
        tiene_controlado = any(d.es_controlado for d in self.detalles)
        tiene_alcohol = any(d.es_alcohol for d in self.detalles)

        if tiene_controlado and tiene_alcohol:
            return False, "Restriccion legal: No esta permitido combinar medicamentos controlados y productos alcoholicos en una misma venta."
        return True, "Carrito valido."

    def procesar_pago(self, efectivo: float = 0.0) -> tuple[bool, str]:
        """Valida el metodo de pago y calcula el cambio correspondiente."""
        if self.metodo_pago.lower() == "efectivo":
            self.efectivo_recibido = float(efectivo)
            if self.efectivo_recibido < self.total_venta:
                faltante = self.total_venta - self.efectivo_recibido
                return False, f"Efectivo insuficiente. Faltan ${faltante:.2f} MXN."
            self.cambio_entregado = round(self.efectivo_recibido - self.total_venta, 2)
            return True, f"Pago completado. Cambio a entregar: ${self.cambio_entregado:.2f} MXN."
        else:
            # Simulacion de pago con tarjeta
            self.efectivo_recibido = self.total_venta
            self.cambio_entregado = 0.0
            return True, "Transaccion bancaria autorizada exitosamente."

    def to_dict(self) -> dict:
        return {
            "id_venta": self.id_venta,
            "id_cliente": self.id_cliente,
            "id_usuario": self.id_usuario,
            "fecha_hora": str(self.fecha_hora),
            "metodo_pago": self.metodo_pago,
            "efectivo_recibido": self.efectivo_recibido,
            "cambio_entregado": self.cambio_entregado,
            "descuento_aplicado": self.descuento_aplicado,
            "total_venta": self.total_venta,
            "detalles": [d.to_dict() for d in self.detalles]
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id_venta, id_cliente, id_usuario, fecha_hora, metodo_pago, efectivo_recibido, cambio_entregado, descuento_aplicado, total_venta)
        return cls(
            id_venta=row[0],
            id_cliente=row[1],
            id_usuario=row[2],
            fecha_hora=row[3],
            metodo_pago=row[4],
            efectivo_recibido=row[5],
            cambio_entregado=row[6],
            descuento_aplicado=row[7],
            total_venta=row[8]
        )

    def __repr__(self):
        return f"<Venta #{self.id_venta} - Total: ${self.total_venta} - Pago: {self.metodo_pago}>"
