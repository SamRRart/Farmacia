import customtkinter as ctk
from tkinter import messagebox, ttk

class PurchasesView(ctk.CTkFrame):
    def __init__(self, parent, role):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuración del diseño interno (Grid)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Título del Módulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Compras a Proveedores y Actualización de Inventario", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal dividido (Formulario a la izquierda | Detalle del Pedido y Totales a la derecha)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- Panel Izquierdo: Registro de Producto en Compra ---
        self.form_frame = ctk.CTkFrame(self.main_container, width=320, corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=(0, 15), pady=0, sticky="nsew")
        self.setup_purchase_form()

        # --- Panel Derecho: Tabla de Detalle de Compra y Confirmación ---
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.setup_provider_header()
        self.setup_purchase_table()
        self.setup_footer_actions()

    def setup_purchase_form(self):
        """Formulario para agregar medicamentos a la orden de compra y actualizar precios."""
        lbl_form = ctk.CTkLabel(self.form_frame, text="Agregar Producto a Orden", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_form.pack(padx=20, pady=(20, 15), anchor="w")

        # Selector / Buscador de Medicamento
        self.entry_med = ctk.CTkEntry(self.form_frame, placeholder_text="Folio o Nombre del Medicamento", width=260, height=38)
        self.entry_med.pack(padx=20, pady=8)

        # Cantidad comprada (Sumará al stock)
        self.entry_cantidad = ctk.CTkEntry(self.form_frame, placeholder_text="Cantidad recibida (+Stock)", width=260, height=38)
        self.entry_cantidad.pack(padx=20, pady=8)

        # Nuevo Precio de Compra
        self.entry_precio_compra = ctk.CTkEntry(self.form_frame, placeholder_text="Precio Compra Unitario ($)", width=260, height=38)
        self.entry_precio_compra.pack(padx=20, pady=8)

        # Nuevo Precio de Venta (Requerimiento: actualizar precios al comprar)
        self.entry_precio_venta = ctk.CTkEntry(self.form_frame, placeholder_text="Nuevo Precio Venta ($)", width=260, height=38)
        self.entry_precio_venta.pack(padx=20, pady=8)

        # Botón Agregar a la Orden
        self.btn_add_item = ctk.CTkButton(
            self.form_frame, text="Agregar a la Orden", fg_color="#2980B9", hover_color="#2471A3",
            command=self.add_to_order, width=260, height=40
        )
        self.btn_add_item.pack(padx=20, pady=(15, 20))

    def setup_provider_header(self):
        """Cabecera para seleccionar el proveedor y estado del pedido."""
        header_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        lbl_prov = ctk.CTkLabel(header_frame, text="Proveedor:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_prov.pack(side="left", padx=(0, 8))

        self.combo_proveedor = ctk.CTkComboBox(
            header_frame, 
            values=["Distribuidora Farmacéutica CUCEI", "Laboratorios PISA", "Genomma Lab", "Bayer de México"],
            width=260, height=35
        )
        self.combo_proveedor.pack(side="left", padx=(0, 15))

        self.combo_estado = ctk.CTkComboBox(
            header_frame,
            values=["Recibido", "Pendiente"],
            width=130, height=35
        )
        self.combo_estado.pack(side="left")
        self.combo_estado.set("Recibido")

    def setup_purchase_table(self):
        """Tabla de detalle de compra (Tabla Detalle_Compras)."""
        table_container = ctk.CTkFrame(self.right_panel)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        columns = ("Medicamento", "Cant.", "P. Compra", "Nuevo P. Venta", "Subtotal")
        self.tree_order = ttk.Treeview(table_container, columns=columns, show="headings", height=12)

        widths = [180, 60, 90, 110, 90]
        for col, w in zip(columns, widths):
            self.tree_order.heading(col, text=col)
            self.tree_order.column(col, width=w, anchor="center")

        self.tree_order.pack(fill="both", expand=True, padx=10, pady=10)

        # Registro simulado de prueba
        self.tree_order.insert("", "end", values=("Amoxicilina 500mg", 50, "$85.00", "$155.00", "$4,250.00"))

    def setup_footer_actions(self):
        """Pie con el total de compra y botón para confirmar y actualizar el inventario."""
        footer_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        footer_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.lbl_total_compra = ctk.CTkLabel(
            footer_frame, text="Total Compra: $4,250.00", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_total_compra.pack(side="left", padx=10)

        self.btn_confirm_purchase = ctk.CTkButton(
            footer_frame, text="Registrar Compra y Actualizar Stock", fg_color="#27AE60", hover_color="#219653",
            command=self.confirm_purchase, width=250, height=42, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_confirm_purchase.pack(side="right", padx=10)

    def add_to_order(self):
        med = self.entry_med.get().strip()
        cant = self.entry_cantidad.get().strip()
        p_compra = self.entry_precio_compra.get().strip()
        p_venta = self.entry_precio_venta.get().strip()

        if not med or not cant or not p_compra or not p_venta:
            messagebox.showerror("Campos incompletos", "Complete todos los campos para agregar el producto a la orden.")
            return

        try:
            cant_int = int(cant)
            pc_float = float(p_compra)
            pv_float = float(p_venta)
            subtotal = cant_int * pc_float

            self.tree_order.insert("", "end", values=(med, cant_int, f"${pc_float:.2f}", f"${pv_float:.2f}", f"${subtotal:,.2f}"))
            self.clear_form()
        except ValueError:
            messagebox.showerror("Dato inválido", "La cantidad debe ser un número entero y los precios deben ser numéricos.")

    def confirm_purchase(self):
        proveedor = self.combo_proveedor.get()
        messagebox.showinfo(
            "Compra Registrada", 
            f"Orden de compra con '{proveedor}' procesada exitosamente.\n\n"
            "• Stock de medicamentos incrementado.\n"
            "• Precios de compra y venta actualizados."
        )

    def clear_form(self):
        self.entry_med.delete(0, 'end')
        self.entry_cantidad.delete(0, 'end')
        self.entry_precio_compra.delete(0, 'end')
        self.entry_precio_venta.delete(0, 'end')