import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.connection import test_connection
from frontend.interfaces.login_window import LoginWindow
from frontend.interfaces.main_dashboard import MainDashboard

def handle_successful_login(role):
    """Función que se ejecuta tras una autenticación exitosa."""
    print(f"Acceso concedido. Abriendo panel para el rol: {role}")
    
    # Instanciamos el Dashboard Principal pasando el rol obtenido
    dashboard = MainDashboard(role=role)
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