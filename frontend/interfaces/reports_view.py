import customtkinter as ctk
from tkinter import messagebox, ttk

class ReportsView(ctk.CTkFrame):
    def __init__(self, parent, role):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuración del diseño interno (Grid)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Título del Módulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Generación de Reportes Gerenciales y Facturación", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal (Filtros arriba | Tabla de resultados abajo)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.setup_filters_panel()
        self.setup_report_table()

    def setup_filters_panel(self):
        """Panel superior para seleccionar tipo de reporte y rangos de fechas/filtros."""
        filter_frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        filter_frame.grid_columnconfigure(5, weight=1)

        # Selector de Tipo de Reporte
        lbl_tipo = ctk.CTkLabel(filter_frame, text="Tipo de Reporte:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_tipo.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.combo_tipo_reporte = ctk.CTkComboBox(
            filter_frame,
            values=[
                "Clientes por Ciudad / Estado", 
                "Ventas por Rango de Fechas", 
                "Compras por Rango de Fechas", 
                "Facturas con Mayores Ventas"
            ],
            width=260, height=35,
            command=self.on_report_type_change
        )
        self.combo_tipo_reporte.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        self.combo_tipo_reporte.set("Clientes por Ciudad / Estado")

        # Filtros de Fechas / Parámetros
        self.entry_param1 = ctk.CTkEntry(filter_frame, placeholder_text="Filtro (Ej. Jalisco / Fecha Ini)", width=180, height=35)
        self.entry_param1.grid(row=0, column=2, padx=10, pady=15, sticky="w")

        self.entry_param2 = ctk.CTkEntry(filter_frame, placeholder_text="Fecha Fin (YYYY-MM-DD)", width=180, height=35)
        self.entry_param2.grid(row=0, column=3, padx=10, pady=15, sticky="w")

        # Botón Generar Reporte
        self.btn_generar = ctk.CTkButton(
            filter_frame, text="Generar Reporte", fg_color="#2980B9", hover_color="#2471A3",
            width=140, height=35, command=self.generate_report
        )
        self.btn_generar.grid(row=0, column=4, padx=15, pady=15, sticky="w")

    def setup_report_table(self):
        """Tabla dinámica para visualizar los resultados del reporte seleccionado."""
        table_container = ctk.CTkFrame(self.main_container)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Columnas iniciales correspondientes a "Clientes por Ciudad / Estado"
        self.columns = ("ID", "Nombre Cliente", "RFC", "Ciudad", "Estado", "Puntos")
        self.tree_report = ttk.Treeview(table_container, columns=self.columns, show="headings", height=15)

        widths = [50, 180, 130, 130, 130, 80]
        for col, w in zip(self.columns, widths):
            self.tree_report.heading(col, text=col)
            self.tree_report.column(col, width=w, anchor="center")

        self.tree_report.pack(fill="both", expand=True, padx=10, pady=10)

        # Cargar datos de muestra iniciales
        self.load_mock_data("Clientes por Ciudad / Estado")

    def on_report_type_change(self, choice):
        """Cambia dinámicamente las columnas de la tabla según el reporte seleccionado."""
        for col in self.tree_report["columns"]:
            self.tree_report.detach(col)
        self.tree_report.delete(*self.tree_report.get_children())

        if choice == "Clientes por Ciudad / Estado":
            self.columns = ("ID", "Nombre Cliente", "RFC", "Ciudad", "Estado", "Puntos")
            widths = [50, 180, 130, 130, 130, 80]
            self.entry_param1.configure(placeholder_text="Ciudad o Estado")
            self.entry_param2.configure(state="normal")
            
        elif choice == "Ventas por Rango de Fechas" or choice == "Compras por Rango de Fechas":
            self.columns = ("ID Transacción", "Fecha / Hora", "Usuario", "Método Pago / Estado", "Total ($)")
            widths = [100, 160, 140, 160, 100]
            self.entry_param1.configure(placeholder_text="Fecha Inicio (YYYY-MM-DD)")
            self.entry_param2.configure(placeholder_text="Fecha Fin (YYYY-MM-DD)")

        elif choice == "Facturas con Mayores Ventas":
            self.columns = ("ID Factura", "ID Venta", "Fecha Emisión", "RFC Receptor", "Monto Venta ($)")
            widths = [90, 90, 160, 140, 110]
            self.entry_param1.configure(placeholder_text="Monto mínimo ($)")
            self.entry_param2.configure(state="disabled")

        self.tree_report.configure(columns=self.columns)
        for col, w in zip(self.columns, widths):
            self.tree_report.heading(col, text=col)
            self.tree_report.column(col, width=w, anchor="center")

        self.load_mock_data(choice)

    def load_mock_data(self, report_type):
        """Carga datos simulados de prueba para la vista previa."""
        if report_type == "Clientes por Ciudad / Estado":
            data = [
                (1, "Juan Pérez Gómez", "PEGJ900101XYZ", "Guadalajara", "Jalisco", 30),
                (2, "María López Ruiz", "LORM850512ABC", "Zapopan", "Jalisco", 50),
                (3, "Carlos Sánchez", "SACC951020DEF", "Monterrey", "Nuevo León", 10)
            ]
        elif report_type == "Ventas por Rango de Fechas":
            data = [
                (101, "2026-05-01 10:30:00", "Encargado 1", "Efectivo", "$520.00"),
                (102, "2026-05-02 14:15:00", "Encargado 2", "Tarjeta", "$1,450.00")
            ]
        elif report_type == "Compras por Rango de Fechas":
            data = [
                (501, "2026-04-28 09:00:00", "Gerente", "Recibido", "$4,250.00"),
                (502, "2026-05-01 11:20:00", "Gerente", "Recibido", "$2,100.00")
            ]
        else: # Facturas con Mayores Ventas
            data = [
                (1, 102, "2026-05-02 14:16:00", "LORM850512ABC", "$1,450.00"),
                (2, 101, "2026-05-01 10:31:00", "PEGJ900101XYZ", "$520.00")
            ]

        for row in data:
            self.tree_report.insert("", "end", values=row)

    def generate_report(self):
        tipo = self.combo_tipo_reporte.get()
        messagebox.showinfo("Reporte Generado", f"El reporte '{tipo}' se ha generado y filtrado correctamente.")