from datetime import datetime

class Factura:
    """
    Representa el comprobante fiscal y documento de facturacion generado por una venta.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(
        self,
        id_factura=None,
        id_venta=None,
        fecha_emision=None,
        rfc_receptor="",
        ruta_archivo_pdf=""
    ):
        self.id_factura = id_factura
        self.id_venta = id_venta
        self.fecha_emision = fecha_emision or datetime.now()
        self.rfc_receptor = rfc_receptor
        self.ruta_archivo_pdf = ruta_archivo_pdf

    def to_dict(self) -> dict:
        return {
            "id_factura": self.id_factura,
            "id_venta": self.id_venta,
            "fecha_emision": str(self.fecha_emision),
            "rfc_receptor": self.rfc_receptor,
            "ruta_archivo_pdf": self.ruta_archivo_pdf
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id_factura, id_venta, fecha_emision, rfc_receptor, ruta_archivo_pdf)
        return cls(
            id_factura=row[0],
            id_venta=row[1],
            fecha_emision=row[2],
            rfc_receptor=row[3],
            ruta_archivo_pdf=row[4]
        )

    def __repr__(self):
        return f"<Factura #{self.id_factura} - Venta:{self.id_venta} - RFC:{self.rfc_receptor}>"
