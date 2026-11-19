class Proveedor:
    """
    Modelo de Proveedor para los laboratorios y distribuidores comerciales.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(self, id_proveedor=None, razon_social="", telefono="", correo=""):
        self.id_proveedor = id_proveedor
        self.razon_social = razon_social
        self.telefono = telefono
        self.correo = correo

    def to_dict(self) -> dict:
        return {
            "id_proveedor": self.id_proveedor,
            "razon_social": self.razon_social,
            "telefono": self.telefono,
            "correo": self.correo
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id_proveedor, razon_social, telefono, correo)
        return cls(
            id_proveedor=row[0],
            razon_social=row[1],
            telefono=row[2] or "",
            correo=row[3] or ""
        )

    def __repr__(self):
        return f"<Proveedor {self.id_proveedor}: {self.razon_social}>"
