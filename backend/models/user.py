import bcrypt

class Usuario:
    """
    Modelo de Usuario que representa a los empleados con acceso al sistema:
    Admin, Gerente y Encargado.
    Basado en el Diagrama de Clases unificado de Farmacia CUCEI.
    """
    def __init__(self, id_usuario=None, perfil="Encargado", nombre="", correo="", password_hash=""):
        self.id_usuario = id_usuario
        self.perfil = perfil
        self.nombre = nombre
        self.correo = correo
        self.password_hash = password_hash

    def verificar_password(self, plain_password: str) -> bool:
        """Verifica si la contraseña en texto plano coincide con el hash bcrypt."""
        if not self.password_hash or not plain_password:
            return False
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

    def to_dict(self) -> dict:
        """Retorna una representación en diccionario sin exponer la contraseña."""
        return {
            "id_usuario": self.id_usuario,
            "perfil": self.perfil,
            "nombre": self.nombre,
            "correo": self.correo
        }

    @classmethod
    def from_row(cls, row):
        """Crea una instancia de Usuario a partir de una tupla de la BD."""
        if not row:
            return None
        # row: (id_usuario, perfil, nombre, correo, password)
        return cls(
            id_usuario=row[0],
            perfil=row[1],
            nombre=row[2],
            correo=row[3],
            password_hash=row[4] if len(row) > 4 else ""
        )

    def __repr__(self):
        return f"<Usuario {self.id_usuario}: {self.nombre} ({self.perfil})>"
