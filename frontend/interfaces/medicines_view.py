import customtkinter as ctk
from tkinter import messagebox, ttk

class MedicinesView(ctk.CTkFrame):
    def __init__(self, parent, role):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuración del diseño interno (Grid)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Título del Módulo
        title_text = "Catálogo y Gestión de Medicamentos" if self.role in ["Admin", "Gerente"] else "Búsqueda y Consulta de Medicamentos"
        self.title_label = ctk.CTkLabel(
            self, 
            text=title_text, 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal dividido (Formulario exclusivo para Admin/Gerente / Tabla a la derecha)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Formulario (Solo se muestra si es Admin o Gerente)
        if self.role in ["Admin", "Gerente"]:
            self.form_frame = ctk.CTkFrame(self.main_container, width=320, corner_radius=10)
            self.form_frame.grid(row=0, column=0, padx=(0, 15), pady=0, sticky="nsew")
            self.setup_form()
            table_col = 1
        else:
            table_col = 0 # Si es encargado, la tabla ocupa todo el ancho

        # --- Panel Derecho: Búsqueda y Tabla de Productos ---
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="transparent")
        self.right_panel.grid(row=0, column=table_col, padx=0, pady=0, sticky="nsew")
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.setup_search_bar()
        self.setup_table()

    def setup_form(self):
        """Configura el formulario CRUD de medicamentos para Admin y Gerente."""
        lbl_form = ctk.CTkLabel(self.form_frame, text="Gestión de Producto", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_form.pack(padx=20, pady=(20, 15), anchor="w")

        self.entry_folio = ctk.CTkEntry(self.form_frame, placeholder_text="Folio", width=260, height=35)
        self.entry_folio.pack(padx=20, pady=6)

        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Nombre del medicamento", width=260, height=35)
        self.entry_nombre.pack(padx=20, pady=6)

        self.entry_categoria = ctk.CTkEntry(self.form_frame, placeholder_text="Clasificación / Categoría", width=260, height=35)
        self.entry_categoria.pack(padx=20, pady=6)

        self.entry_pcompra = ctk.CTkEntry(self.form_frame, placeholder_text="Precio Compra ($)", width=260, height=35)
        self.entry_pcompra.pack(padx=20, pady=6)

        self.entry_pventa = ctk.CTkEntry(self.form_frame, placeholder_text="Precio Venta ($)", width=260, height=35)
        self.entry_pventa.pack(padx=20, pady=6)

        self.entry_stock = ctk.CTkEntry(self.form_frame, placeholder_text="Stock inicial", width=260, height=35)
        self.entry_stock.pack(padx=20, pady=6)

        # Botón Guardar / Registrar
        self.btn_guardar = ctk.CTkButton(
            self.form_frame, text="Guardar Medicamento", fg_color="#27AE60", hover_color="#219653",
            command=self.save_medicine, width=260, height=38
        )
        self.btn_guardar.pack(padx=20, pady=(15, 20))

    def setup_search_bar(self):
        """Barra de búsqueda rápida para encontrar medicamentos por nombre o categoría."""
        self.search_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.entry_search = ctk.CTkEntry(self.search_frame, placeholder_text="Buscar medicamento por nombre o categoría...", width=320, height=35)
        self.entry_search.pack(side="left", padx=(0, 10))

        self.btn_search = ctk.CTkButton(self.search_frame, text="Buscar", width=100, height=35, command=self.search_medicine)
        self.btn_search.pack(side="left")

    def setup_table(self):
        """Tabla para mostrar el inventario de medicamentos."""
        table_container = ctk.CTkFrame(self.right_panel)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        columns = ("ID", "Folio", "Nombre", "Categoría", "P. Venta", "Stock")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=15)
        
        widths = [40, 70, 160, 110, 80, 70]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Cargar datos simulados (Tabla Productos de PostgreSQL)
        self.load_mock_medicines()

    def load_mock_medicines(self):
        """Simula registros de medicamentos."""
        mock_data = [
            (1, "MED-001", "Paracetamol 500mg", "Analgésico", "$45.50", 120),
            (2, "MED-002", "Ibuprofeno 400mg", "Analgésico", "$60.00", 85),
            (3, "MED-003", "Amoxicilina 500g", "Antibiótico", "$150.00", 40),
            (4, "MED-004", "Loratadina 10mg", "Antihistamínico", "$85.00", 95)
        ]
        for row in mock_data:
            self.tree.insert("", "end", values=row)

    def save_medicine(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre del medicamento es obligatorio.")
            return
        messagebox.showinfo("Éxito", f"Medicamento {nombre} guardado correctamente.")
        self.clear_form()

    def search_medicine(self):
        query = self.entry_search.get().strip()
        messagebox.showinfo("Búsqueda", f"Buscando producto: {query}")

    def clear_form(self):
        self.entry_folio.delete(0, 'end')
        self.entry_nombre.delete(0, 'end')
        self.entry_categoria.delete(0, 'end')
        self.entry_pcompra.delete(0, 'end')
        self.entry_pventa.delete(0, 'end')
        self.entry_stock.delete(0, 'end')