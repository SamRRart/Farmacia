from datetime import datetime

class DetalleCompra:
    """
    Representa una linea de detalle dentro de una orden de compra a proveedor.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(
        self,
        id_detalle_compra=None,
        id_compra=None,
        id_producto=None,
        cantidad=1,
        precio_compra_unitario=0.0,
        subtotal=0.0,
        producto_nombre="",
        producto_folio=""
    ):
        self.id_detalle_compra = id_detalle_compra
        self.id_compra = id_compra
        self.id_producto = id_producto
        self.cantidad = int(cantidad)
        self.precio_compra_unitario = float(precio_compra_unitario)
        self.subtotal = float(subtotal) if subtotal else self.calcular_subtotal()
        self.producto_nombre = producto_nombre
        self.producto_folio = producto_folio

    def calcular_subtotal(self) -> float:
        """Calcula el subtotal multiplicando la cantidad por el precio unitario."""
        self.subtotal = round(self.cantidad * self.precio_compra_unitario, 2)
        return self.subtotal

    def to_dict(self) -> dict:
        return {
            "id_detalle_compra": self.id_detalle_compra,
            "id_compra": self.id_compra,
            "id_producto": self.id_producto,
            "producto_nombre": self.producto_nombre,
            "producto_folio": self.producto_folio,
            "cantidad": self.cantidad,
            "precio_compra_unitario": self.precio_compra_unitario,
            "subtotal": self.subtotal
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id_detalle_compra, id_compra, id_producto, cantidad, precio_compra_unitario, subtotal)
        return cls(
            id_detalle_compra=row[0],
            id_compra=row[1],
            id_producto=row[2],
            cantidad=row[3],
            precio_compra_unitario=row[4],
            subtotal=row[5]
        )

    def __repr__(self):
        return f"<DetalleCompra Prod:{self.id_producto} Cant:{self.cantidad} Subtotal:${self.subtotal}>"


class Compra:
    """
    Representa una orden de compra o reabastecimiento (Restock) a un proveedor.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(
        self,
        id_compra=None,
        id_proveedor=None,
        id_usuario=None,
        fecha_hora=None,
        estado_pedido="Enviado",
        total_compra=0.0,
        proveedor_nombre="",
        usuario_nombre="",
        detalles=None
    ):
        self.id_compra = id_compra
        self.id_proveedor = id_proveedor
        self.id_usuario = id_usuario
        self.fecha_hora = fecha_hora or datetime.now()
        self.estado_pedido = estado_pedido
        self.total_compra = float(total_compra)
        self.proveedor_nombre = proveedor_nombre
        self.usuario_nombre = usuario_nombre
        self.detalles = detalles if detalles is not None else []

    def agregar_detalle(self, detalle: DetalleCompra) -> None:
        """Agrega un producto a la lista de detalles y recalcula el total."""
        self.detalles.append(detalle)
        self.calcular_total()

    def calcular_total(self) -> float:
        """Calcula la suma de todos los subtotales de la orden."""
        self.total_compra = round(sum(d.calcular_subtotal() for d in self.detalles), 2)
        return self.total_compra

    def marcar_como_surtido(self) -> None:
        """Cambia el estado de la compra a Surtido."""
        self.estado_pedido = "Surtido"

    def to_dict(self) -> dict:
        return {
            "id_compra": self.id_compra,
            "id_proveedor": self.id_proveedor,
            "proveedor_nombre": self.proveedor_nombre,
            "id_usuario": self.id_usuario,
            "usuario_nombre": self.usuario_nombre,
            "fecha_hora": str(self.fecha_hora),
            "estado_pedido": self.estado_pedido,
            "total_compra": self.total_compra,
            "detalles": [d.to_dict() for d in self.detalles]
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id_compra, id_proveedor, id_usuario, fecha_hora, estado_pedido, total_compra)
        return cls(
            id_compra=row[0],
            id_proveedor=row[1],
            id_usuario=row[2],
            fecha_hora=row[3],
            estado_pedido=row[4],
            total_compra=row[5]
        )

    def __repr__(self):
        return f"<Compra {self.id_compra} - Prov:{self.id_proveedor} - Estado:{self.estado_pedido} - Total:${self.total_compra}>"
