import customtkinter as ctk
from tkinter import messagebox

class MainDashboard(ctk.CTk):
    def __init__(self, role, username="Usuario"):
        super().__init__()
        self.role = role
        self.username = username

        # Configuración de la ventana principal
        self.title(f"Farmacia CUCEI - Panel Principal [{self.role}]")
        self.geometry("1024x680")
        self.minsize(800, 600)

        # Configuración de la retícula principal (Grid: Sidebar + Contenido)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Panel Lateral (Sidebar)
        self.create_sidebar()

        # 2. Área de Contenido Principal (Frame dinámico)
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Cargar vista por defecto según el rol
        self.load_default_view()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)  # Empujar elementos hacia arriba

        # Título del Menú
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Farmacia CUCEI", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Indicador de Rol
        self.role_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text=f"Rol: {self.role}", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray"
        )
        self.role_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # --- BOTONES DINÁMICOS SEGÚN EL ROL ---
        current_row = 2

        # Ventas (Disponible para Encargado, Gerente y Admin)
        if self.role in ["Admin", "Gerente", "Encargado"]:
            self.btn_sales = ctk.CTkButton(
                self.sidebar_frame, text="🛒 Ventas / POS", command=self.show_sales_view
            )
            self.btn_sales.grid(row=current_row, column=0, padx=20, pady=10, sticky="ew")
            current_row += 1

        # Clientes (Disponible para todos)
        if self.role in ["Admin", "Gerente", "Encargado"]:
            self.btn_clients = ctk.CTkButton(
                self.sidebar_frame, text="👥 Clientes y Puntos", command=self.show_clients_view
            )
            self.btn_clients.grid(row=current_row, column=0, padx=20, pady=10, sticky="ew")
            current_row += 1

        # Medicamentos / Productos (Búsqueda o CRUD completo)
        if self.role in ["Admin", "Gerente", "Encargado"]:
            self.btn_medicines = ctk.CTkButton(
                self.sidebar_frame, text="💊 Medicamentos", command=self.show_medicines_view
            )
            self.btn_medicines.grid(row=current_row, column=0, padx=20, pady=10, sticky="ew")
            current_row += 1

        # Compras a Proveedores (Exclusivo Gerente y Admin)
        if self.role in ["Admin", "Gerente"]:
            self.btn_purchases = ctk.CTkButton(
                self.sidebar_frame, text="📦 Compras Proveedores", command=self.show_purchases_view
            )
            self.btn_purchases.grid(row=current_row, column=0, padx=20, pady=10, sticky="ew")
            current_row += 1

        # Control de Usuarios (Exclusivo Admin y parcialmente Gerente)
        if self.role in ["Admin", "Gerente"]:
            self.btn_users = ctk.CTkButton(
                self.sidebar_frame, text="🔐 Control de Usuarios", command=self.show_users_view
            )
            self.btn_users.grid(row=current_row, column=0, padx=20, pady=10, sticky="ew")
            current_row += 1

        # Reportes (Exclusivo Gerente y Admin)
        if self.role in ["Admin", "Gerente"]:
            self.btn_reports = ctk.CTkButton(
                self.sidebar_frame, text="📊 Reportes del Sistema", command=self.show_reports_view
            )
            self.btn_reports.grid(row=current_row, column=0, padx=20, pady=10, sticky="ew")
            current_row += 1

        # Botón de Cerrar Sesión (Inferior)
        self.btn_logout = ctk.CTkButton(
            self.sidebar_frame, text="Cerrar Sesión", fg_color="#C0392B", hover_color="#962D22",
            command=self.logout
        )
        self.btn_logout.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

    def clear_content(self):
        """Destruye los widgets actuales en el área de contenido para cargar una nueva vista."""
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def load_default_view(self):
        self.clear_content()
        welcome_label = ctk.CTkLabel(
            self.content_area, 
            text=f"Bienvenido al Sistema Farmacia CUCEI\nHas ingresado como: {self.role}", 
            font=ctk.CTkFont(size=22, weight="bold"),
            justify="center"
        )
        welcome_label.pack(expand=True, anchor="center")

    def show_sales_view(self):
        self.clear_content()
        ctk.CTkLabel(self.content_area, text="Módulo de Ventas / Punto de Venta (POS)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        # Aquí se integrará posteriormente sales_view.py

    def show_clients_view(self):
        self.clear_content()
        ctk.CTkLabel(self.content_area, text="Control de Clientes y Acumulación de Puntos", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        # Aquí se integrará clients_view.py

    def show_medicines_view(self):
        self.clear_content()
        ctk.CTkLabel(self.content_area, text="Catálogo y Gestión de Medicamentos", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        # Aquí se integrará medicines_view.py

    def show_purchases_view(self):
        self.clear_content()
        ctk.CTkLabel(self.content_area, text="Módulo de Compras a Proveedores y Actualización de Stock", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        # Aquí se integrará purchases_view.py

    def show_users_view(self):
        self.clear_content()
        # Importamos e instanciamos la vista de usuarios dentro del content_area
        from frontend.interfaces.users_view import UsersView
        users_view = UsersView(parent=self.content_area, role=self.role)
        users_view.pack(fill="both", expand=True)

    def show_reports_view(self):
        self.clear_content()
        ctk.CTkLabel(self.content_area, text="Generación de Reportes Gerenciales y Facturas", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

    def logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea salir del sistema?"):
            self.destroy()
            # Opcional: Volver a abrir la ventana de login
            from frontend.interfaces.login_window import LoginWindow
            app = LoginWindow(on_login_success=lambda r: MainDashboard(r).mainloop())
            app.mainloop()

if __name__ == "__main__":
    # Prueba unitaria simulando un rol de Gerente
    app = MainDashboard(role="Gerente")
    app.mainloop()