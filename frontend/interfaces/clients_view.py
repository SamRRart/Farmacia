import customtkinter as ctk
from tkinter import messagebox, ttk
from backend.services.client_service import get_all_clients, create_client

class ClientsView(ctk.CTkFrame):
    def __init__(self, parent, role):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuración del diseño interno (Grid)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Título del Módulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Control de Clientes y Acumulación de Puntos", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal dividido (Formulario a la izquierda / Tabla y búsqueda a la derecha)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- Panel Izquierdo: Formulario de Registro de Clientes ---
        self.form_frame = ctk.CTkFrame(self.main_container, width=320, corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=(0, 15), pady=0, sticky="nsew")
        
        self.setup_form()

        # --- Panel Derecho: Tabla y Búsqueda ---
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.setup_search_bar()
        self.setup_table()

    def setup_form(self):
        """Configura los campos del formulario para registrar clientes y asignar puntos/RFC."""
        lbl_form = ctk.CTkLabel(self.form_frame, text="Registrar / Editar Cliente", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_form.pack(padx=20, pady=(20, 15), anchor="w")

        # Nombre
        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Nombre completo", width=260, height=40)
        self.entry_nombre.pack(padx=20, pady=8)

        # Teléfono
        self.entry_telefono = ctk.CTkEntry(self.form_frame, placeholder_text="Teléfono", width=260, height=40)
        self.entry_telefono.pack(padx=20, pady=8)

        # RFC (Clave para asignación de puntos y facturación)
        self.entry_rfc = ctk.CTkEntry(self.form_frame, placeholder_text="RFC (13 caracteres)", width=260, height=40)
        self.entry_rfc.pack(padx=20, pady=8)

        # Correo (Para envío de facturas en PDF)
        self.entry_correo = ctk.CTkEntry(self.form_frame, placeholder_text="Correo electrónico", width=260, height=40)
        self.entry_correo.pack(padx=20, pady=8)

        # Fecha de Nacimiento
        self.entry_fnac = ctk.CTkEntry(self.form_frame, placeholder_text="Fecha Nacimiento (YYYY-MM-DD)", width=260, height=40)
        self.entry_fnac.pack(padx=20, pady=8)

        # Botón Guardar Cliente
        self.btn_guardar = ctk.CTkButton(
            self.form_frame, text="Guardar Cliente", fg_color="#27AE60", hover_color="#219653",
            command=self.save_client, width=260, height=40
        )
        self.btn_guardar.pack(padx=20, pady=(20, 20))

    def setup_search_bar(self):
        """Barra superior de búsqueda por RFC o Nombre."""
        self.search_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.entry_search = ctk.CTkEntry(self.search_frame, placeholder_text="Buscar por Nombre o RFC...", width=300, height=35)
        self.entry_search.pack(side="left", padx=(0, 10))

        self.btn_search = ctk.CTkButton(self.search_frame, text="Buscar", width=100, height=35, command=self.search_client)
        self.btn_search.pack(side="left")

    def setup_table(self):
        """Configura la tabla para visualizar clientes y sus puntos acumulados."""
        table_container = ctk.CTkFrame(self.right_panel)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        columns = ("ID", "Nombre", "Teléfono", "RFC", "Correo", "Puntos")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=15)
        
        widths = [40, 140, 90, 110, 160, 70]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Cargar datos simulados (corresponden a la tabla Clientes en PostgreSQL)
        self.load_mock_clients()

    def load_clients_data(self):
        """Obtiene los clientes del backend y los muestra en la interfaz gráfica."""
        clients = get_all_clients()
        # Itera sobre 'clients' para poblar tu tabla visual (ej. Treeview o CTkTable)
        for client in clients:
            id_cliente, nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados = client
            # Inserta los datos en la tabla de la interfaz...
            self.tree.insert("", "end", values=(id_cliente, nombre, telefono, rfc, correo, puntos_acumulados))

    def save_client(self):
        nombre = self.entry_nombre.get().strip()
        rfc = self.entry_rfc.get().strip()
        
        if not nombre or not rfc:
            messagebox.showerror("Error", "El nombre y el RFC son obligatorios para el control de puntos.")
            return

        messagebox.showinfo("Éxito", f"Cliente {nombre} registrado correctamente.")
        self.clear_form()

    def search_client(self):
        query = self.entry_search.get().strip()
        messagebox.showinfo("Búsqueda", f"Buscando cliente: {query}")

    def clear_form(self):
        self.entry_nombre.delete(0, 'end')
        self.entry_telefono.delete(0, 'end')
        self.entry_rfc.delete(0, 'end')
        self.entry_correo.delete(0, 'end')
        self.entry_fnac.delete(0, 'end')