import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.connection import test_connection
from frontend.interfaces.login_window import LoginWindow
from frontend.interfaces.main_dashboard import MainDashboard

def handle_successful_login(user_info):
    """Función que se ejecuta tras una autenticación exitosa."""
    if isinstance(user_info, dict):
        role = user_info.get("perfil", "Encargado")
        username = user_info.get("nombre", "Usuario")
        user_id = user_info.get("id_usuario")
    else:
        role = str(user_info)
        username = "Usuario"
        user_id = None

    print(f"Acceso concedido. Abriendo panel para: {username} [{role}]")
    
    # Instanciamos el Dashboard Principal pasando rol, nombre y user_id
    dashboard = MainDashboard(role=role, username=username, user_id=user_id)
    dashboard.mainloop()

def main():
    print("========================================")
    print("       FARMACIA CUCEI - SISTEMA         ")
    print("========================================")

    try:
        test_connection()
    except Exception as e:
        print(f"[Aviso] Conexión a BD: {e}")

    # Lanzamos la ventana de Login
    login_app = LoginWindow(on_login_success=handle_successful_login)
    login_app.mainloop()

if __name__ == "__main__":
    main()