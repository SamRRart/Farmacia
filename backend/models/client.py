class Cliente:
    """
    Modelo de Cliente que almacena la informacion personal y el programa de puntos.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(
        self,
        id_cliente=None,
        nombre="",
        telefono="",
        rfc="",
        correo="",
        fecha_nacimiento=None,
        puntos_acumulados=0,
        ciudad="",
        estado=""
    ):
        self.id_cliente = id_cliente
        self.nombre = nombre
        self.telefono = telefono
        self.rfc = rfc
        self.correo = correo
        self.fecha_nacimiento = fecha_nacimiento
        self.puntos_acumulados = int(puntos_acumulados) if puntos_acumulados else 0
        self.ciudad = ciudad
        self.estado = estado

    def calcular_puntos_ganados(self, total_compra: float) -> int:
        """
        Regla de negocio: Por cada compra mayor a $500.00 MXN,
        se asignan 10 puntos al cliente.
        """
        if float(total_compra) > 500.00:
            return 10
        return 0

    def evaluar_descuento(self) -> bool:
        """
        Regla de negocio: Al llegar a 50 puntos o mas,
        el cliente es acreedor a un 10% de descuento en su compra.
        """
        return self.puntos_acumulados >= 50

    def resetear_puntos(self) -> None:
        """Resetea los puntos a cero una vez aplicado el descuento de lealtad."""
        self.puntos_acumulados = 0

    def to_dict(self) -> dict:
        return {
            "id_cliente": self.id_cliente,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "rfc": self.rfc,
            "correo": self.correo,
            "fecha_nacimiento": str(self.fecha_nacimiento) if self.fecha_nacimiento else "",
            "puntos_acumulados": self.puntos_acumulados,
            "ciudad": self.ciudad,
            "estado": self.estado
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id_cliente, nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados, ciudad, estado)
        return cls(
            id_cliente=row[0],
            nombre=row[1],
            telefono=row[2] or "",
            rfc=row[3] or "",
            correo=row[4] or "",
            fecha_nacimiento=row[5],
            puntos_acumulados=row[6] if len(row) > 6 and row[6] is not None else 0,
            ciudad=row[7] if len(row) > 7 and row[7] else "",
            estado=row[8] if len(row) > 8 and row[8] else ""
        )

    def __repr__(self):
        return f"<Cliente {self.id_cliente}: {self.nombre} ({self.rfc}) - Puntos: {self.puntos_acumulados}>"
