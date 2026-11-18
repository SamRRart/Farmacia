import socket

def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: float = 2.0) -> bool:
    """
    Comprueba si el equipo cuenta con una conexion a internet activa y funcional.
    Realiza un intento rapido de conexion por socket hacia un servidor DNS publico.
    Retorna True si hay conexion; False si la red esta desconectada.
    """
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except (socket.timeout, socket.error, OSError):
        # Intento secundario con Cloudflare DNS en caso de bloqueo de puerto 53
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect(("1.1.1.1", 53))
            s2.close()
            return True
        except (socket.timeout, socket.error, OSError):
            return False
