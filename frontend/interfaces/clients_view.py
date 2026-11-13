import customtkinter as ctk
from backend.services.client_service import get_all_clients, create_client, search_clients

class ClientsView(ctk.CTkFrame):
    def __init__(self, parent, role=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.role = role
        
        # Ocupar todo el espacio principal del dashboard
        self.pack(fill="both", expand=True)
        
        # Título superior de la vista
        self.title_label = ctk.CTkLabel(
            self, 
            text="Catálogo y Gestión de Clientes", 
            font=("Arial", 20, "bold")
        )
        self.title_label.pack(anchor="w", padx=20, pady=(15, 10))

        # Contenedor principal dividido en dos columnas (Izquierda: Formulario, Derecha: Tabla y Buscador)
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # --- PANEL IZQUIERDO: Gestión de Cliente (Formulario) ---
        left_panel = ctk.CTkFrame(main_container, width=320, corner_radius=8)
        left_panel.pack(side="left", fill="y", padx=(0, 15), pady=0)
        left_panel.pack_propagate(False) 
        
        form_title = ctk.CTkLabel(left_panel, text="Gestión de Cliente", font=("Arial", 16, "bold"))
        form_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Campos de entrada
        self.entry_nombre = ctk.CTkEntry(left_panel, placeholder_text="Nombre completo")
        self.entry_nombre.pack(fill="x", padx=15, pady=8)
        
        self.entry_telefono = ctk.CTkEntry(left_panel, placeholder_text="Teléfono")
        self.entry_telefono.pack(fill="x", padx=15, pady=8)
        
        self.entry_rfc = ctk.CTkEntry(left_panel, placeholder_text="RFC")
        self.entry_rfc.pack(fill="x", padx=15, pady=8)
        
        self.entry_correo = ctk.CTkEntry(left_panel, placeholder_text="Correo electrónico")
        self.entry_correo.pack(fill="x", padx=15, pady=8)
        
        self.entry_naci = ctk.CTkEntry(left_panel, placeholder_text="Fecha Nac. (YYYY-MM-DD)")
        self.entry_naci.pack(fill="x", padx=15, pady=8)
        
        # Botón verde de guardar
        self.btn_save = ctk.CTkButton(
            left_panel, 
            text="Guardar Cliente", 
            fg_color="#28a745", 
            hover_color="#218838",
            command=self.save_client
        )
        self.btn_save.pack(side="bottom", fill="x", padx=15, pady=15)

        # --- PANEL DERECHO: Buscador y Tabla de Registros ---
        right_panel = ctk.CTkFrame(main_container, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Barra superior de búsqueda
        search_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        
        self.entry_search = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Buscar cliente por nombre, RFC o correo...", 
            height=35
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<Return>", lambda event: self.perform_search()) # Permitir buscar con Enter
        
        self.btn_search = ctk.CTkButton(
            search_frame, 
            text="Buscar", 
            width=100, 
            height=35,
            command=self.perform_search
        )
        self.btn_search.pack(side="right")

        # Contenedor estilo tarjeta blanca para la tabla
        table_card = ctk.CTkFrame(right_panel, fg_color=("white", "gray15"), corner_radius=8)
        table_card.pack(fill="both", expand=True)
        
        # Fila de Encabezados de la tabla
        headers_frame = ctk.CTkFrame(table_card, fg_color=("gray90", "gray25"), corner_radius=4)
        headers_frame.pack(fill="x", padx=10, pady=10)
        
        columns_config = [
            ("ID", 40), 
            ("Nombre", 180), 
            ("Teléfono", 90), 
            ("RFC", 110), 
            ("Correo", 170), 
            ("Puntos", 60)
        ]
        
        for text, width in columns_config:
            lbl = ctk.CTkLabel(headers_frame, text=text, font=("Arial", 11, "bold"), width=width, anchor="w")
            lbl.pack(side="left", padx=4, pady=6)

        # Área con scroll para las filas de datos
        self.scroll_table = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Cargar los registros iniciales
        self.load_table_data()

    def load_table_data(self):
        """Consulta el backend y pinta todos los clientes en la tabla."""
        clients = get_all_clients()
        self.populate_table(clients)

    def perform_search(self):
        """Realiza la búsqueda filtrada basada en el texto ingresado."""
        term = self.entry_search.get().strip()
        if not term:
            self.load_table_data()
            return
            
        clients = search_clients(term)
        self.populate_table(clients)

    def populate_table(self, clients):
        """Método auxiliar para limpiar y rellenar la tabla con una lista de clientes."""
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
            
        if not clients:
            empty_lbl = ctk.CTkLabel(self.scroll_table, text="No se encontraron registros.", text_color="gray")
            empty_lbl.pack(pady=20)
            return
            
        for client in clients:
            id_cliente, nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados = client
            
            row = ctk.CTkFrame(self.scroll_table, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            row_data = [
                (str(id_cliente), 40),
                (str(nombre), 180),
                (str(telefono), 90),
                (str(rfc), 110),
                (str(correo), 170),
                (str(puntos_acumulados), 60)
            ]
            
            for text, width in row_data:
                cell = ctk.CTkLabel(row, text=text, font=("Arial", 11), width=width, anchor="w")
                cell.pack(side="left", padx=4, pady=4)

    def save_client(self):
        """Captura los datos del formulario izquierdo y los guarda en la base de datos."""
        nombre = self.entry_nombre.get().strip()
        telefono = self.entry_telefono.get().strip()
        rfc = self.entry_rfc.get().strip()
        correo = self.entry_correo.get().strip()
        fecha_naci = self.entry_naci.get().strip()
        
        if not nombre or not telefono:
            print("[Advertencia]: Nombre y teléfono son obligatorios.")
            return
            
        success = create_client(nombre, telefono, rfc, correo, fecha_naci)
        if success:
            print("[Éxito]: Cliente guardado correctamente.")
            # Limpiar campos
            self.entry_nombre.delete(0, 'end')
            self.entry_telefono.delete(0, 'end')
            self.entry_rfc.delete(0, 'end')
            self.entry_correo.delete(0, 'end')
            self.entry_naci.delete(0, 'end')
            # Recargar la tabla
            self.load_table_data()
        else:
            print("[Error]: No se pudo registrar el cliente.")