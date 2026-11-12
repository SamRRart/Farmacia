import customtkinter as ctk
from tkinter import messagebox, ttk

class UsersView(ctk.CTkFrame):
    def __init__(self, parent, role):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuración del diseño interno (Grid)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Título del Módulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Gestión y Control de Usuarios", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal dividido (Formulario a la izquierda / Tabla a la derecha)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- Panel Izquierdo: Formulario de Registro ---
        self.form_frame = ctk.CTkFrame(self.main_container, width=320, corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=(0, 15), pady=0, sticky="nsew")
        
        self.setup_form()

        # --- Panel Derecho: Tabla / Lista de Usuarios ---
        self.table_frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.table_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.setup_table()

    def setup_form(self):
        """Configura los campos del formulario para dar de alta usuarios."""
        lbl_form = ctk.CTkLabel(self.form_frame, text="Registrar / Editar Usuario", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_form.pack(padx=20, pady=(20, 15), anchor="w")

        # Nombre
        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Nombre completo", width=260, height=40)
        self.entry_nombre.pack(padx=20, pady=10)

        # Correo
        self.entry_correo = ctk.CTkEntry(self.form_frame, placeholder_text="Correo electrónico", width=260, height=40)
        self.entry_correo.pack(padx=20, pady=10)

        # Contraseña
        self.entry_password = ctk.CTkEntry(self.form_frame, placeholder_text="Contraseña", show="*", width=260, height=40)
        self.entry_password.pack(padx=20, pady=10)

        # Selector de Perfil / Rol
        # Nota: El Administrador puede asignar cualquier rol, el Gerente puede dar de alta encargados según reglas de negocio.
        roles_disponibles = ["Admin", "Gerente", "Encargado"] if self.role == "Admin" else ["Encargado"]
        
        self.combo_rol = ctk.CTkComboBox(self.form_frame, values=roles_disponibles, width=260, height=40)
        self.combo_rol.pack(padx=20, pady=10)
        if roles_disponibles:
            self.combo_rol.set(roles_disponibles[0])

        # Botón Guardar
        self.btn_guardar = ctk.CTkButton(
            self.form_frame, text="Guardar Usuario", fg_color="#27AE60", hover_color="#219653",
            command=self.save_user, width=260, height=40
        )
        self.btn_guardar.pack(padx=20, pady=(20, 20))

    def setup_table(self):
        """Configura la tabla visual para listar los usuarios registrados."""
        # Nota: Usamos ttk.Treeview integrado con CustomTkinter para mostrar filas y columnas limpias
        columns = ("ID", "Nombre", "Correo", "Perfil")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Cargar datos de prueba iniciales (simulando consulta a tabla Usuarios de PostgreSQL)
        self.load_mock_users()

    def load_mock_users(self):
        """Simula la carga de usuarios desde la base de datos."""
        mock_data = [
            (1, "Administrador General", "admin@cucei.udg.mx", "Admin"),
            (2, "Gerente de Sucursal", "gerente@cucei.udg.mx", "Gerente"),
            (3, "Encargado Turno Matutino", "encargado1@cucei.udg.mx", "Encargado")
        ]
        for row in mock_data:
            self.tree.insert("", "end", values=row)

    def save_user(self):
        nombre = self.entry_nombre.get().strip()
        correo = self.entry_correo.get().strip()
        password = self.entry_password.get().strip()
        perfil = self.combo_rol.get()

        if not nombre or not correo or not password:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        # TODO: Aquí se conectará con el backend para insertar el registro en la tabla `Usuarios` de PostgreSQL
        messagebox.showinfo("Éxito", f"Usuario {nombre} registrado correctamente como {perfil}.")
        
        # Limpiar campos y refrescar tabla
        self.entry_nombre.delete(0, 'end')
        self.entry_correo.delete(0, 'end')
        self.entry_password.delete(0, 'end')