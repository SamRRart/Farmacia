import customtkinter as ctk
from tkinter import messagebox
from backend.services.user_service import authenticate_db_user

# Configuración global de CustomTkinter
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success

        # Configuración de la ventana principal de Login
        self.title("Farmacia CUCEI - Acceso al Sistema")
        self.geometry("420x520")
        self.resizable(False, False)

        # Centrar ventana en pantalla
        self.center_window()

        # Contenedor / Marco principal
        self.frame = ctk.CTkFrame(self, corner_radius=15)
        self.frame.pack(fill="both", expand=True, padx=30, pady=30)
        self.frame.pack_propagate(False)
        
        # Título y subtítulo
        self.title_label = ctk.CTkLabel(
            self.frame, 
            text="Farmacia CUCEI", 
            font=ctk.CTkFont(size=26, weight="bold")
        )
        self.title_label.pack(pady=(40, 10))

        self.subtitle_label = ctk.CTkLabel(
            self.frame, 
            text="Inicie sesión con sus credenciales", 
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 30))

        # Campo de Usuario
        self.username_entry = ctk.CTkEntry(
            self.frame, 
            placeholder_text="Usuario", 
            width=280, 
            height=45,
            corner_radius=8
        )
        self.username_entry.pack(pady=12)

        # Campo de Contraseña
        self.password_entry = ctk.CTkEntry(
            self.frame, 
            placeholder_text="Contraseña", 
            show="*", 
            width=280, 
            height=45,
            corner_radius=8
        )
        self.password_entry.pack(pady=12)

        # Botón de Inicio de Sesión
        self.login_button = ctk.CTkButton(
            self.frame, 
            text="Ingresar", 
            command=self.handle_login, 
            width=280, 
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.login_button.pack(pady=(30, 20))

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Campos vacíos", "Por favor, ingrese usuario y contraseña.")
            return

        # TODO: Aquí se reemplazará por la consulta real al servicio de autenticación y PostgreSQL
        role = self.authenticate_user(username, password)

        if role:
            messagebox.showinfo("Acceso Exitoso", f"Bienvenido al sistema.\nRol detectado: {role}")
            self.destroy()
            self.on_login_success(role)
        else:
            messagebox.showerror("Error de Autenticación", "Usuario o contraseña incorrectos.")

    def authenticate_user(self, username, password):
        """Consulta la base de datos real a través del servicio."""
        role = authenticate_db_user(username, password)
        return role

if __name__ == "__main__":
    app = LoginWindow(on_login_success=lambda r: print(f"Iniciado como: {r}"))
    app.mainloop()