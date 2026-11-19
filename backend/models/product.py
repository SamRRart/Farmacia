class Producto:
    """
    Modelo de Producto que representa cualquier articulo comercializado por la farmacia:
    Medicamentos, Bebidas alcoholicas, Despensa, Cuidado Personal, etc.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(
        self,
        id_producto=None,
        id_proveedor=None,
        folio="",
        nombre="",
        categoria="",
        precio_compra=0.0,
        precio_venta=0.0,
        stock=0,
        es_controlado=False,
        es_alcohol=False
    ):
        self.id_producto = id_producto
        self.id_proveedor = id_proveedor
        self.folio = folio
        self.nombre = nombre
        self.categoria = categoria
        self.precio_compra = float(precio_compra)
        self.precio_venta = float(precio_venta)
        self.stock = int(stock)
        self.es_controlado = bool(es_controlado)
        self.es_alcohol = bool(es_alcohol)

    def actualizar_stock(self, cantidad: int) -> None:
        """Actualiza el stock sumando o restando la cantidad indicada."""
        self.stock += cantidad

    def verificar_disponibilidad(self, cantidad: int) -> bool:
        """Comprueba si hay suficiente stock para cubrir la cantidad solicitada."""
        return self.stock >= cantidad

    def to_dict(self) -> dict:
        """Retorna una representacion en diccionario para interfaces o reportes."""
        return {
            "id_producto": self.id_producto,
            "id_proveedor": self.id_proveedor,
            "folio": self.folio,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "precio_compra": self.precio_compra,
            "precio_venta": self.precio_venta,
            "stock": self.stock,
            "es_controlado": self.es_controlado,
            "es_alcohol": self.es_alcohol
        }

    @classmethod
    def from_row(cls, row):
        """Construye una instancia a partir de una fila de la BD."""
        if not row:
            return None
        # row: (id_producto, id_proveedor, folio, nombre, categoria, precio_compra, precio_venta, stock, es_controlado, es_alcohol)
        return cls(
            id_producto=row[0],
            id_proveedor=row[1],
            folio=row[2] or "",
            nombre=row[3],
            categoria=row[4] or "",
            precio_compra=row[5],
            precio_venta=row[6],
            stock=row[7] if row[7] is not None else 0,
            es_controlado=row[8] if row[8] is not None else False,
            es_alcohol=row[9] if row[9] is not None else False
        )

    def __repr__(self):
        return f"<Producto {self.id_producto} ({self.folio}): {self.nombre} - Stock: {self.stock}>"
