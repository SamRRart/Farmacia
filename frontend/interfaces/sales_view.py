import customtkinter as ctk
from tkinter import messagebox, ttk

class SalesView(ctk.CTkFrame):
    def __init__(self, parent, role):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuración del diseño interno (Grid)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Título del Módulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Punto de Venta (POS) - Farmacia CUCEI", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal (Carrito / Productos a la izquierda | Datos de Cliente y Totales a la derecha)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=2)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- Panel Izquierdo: Selección de Productos y Carrito ---
        self.left_panel = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.setup_product_selector()
        self.setup_cart_table()

        # --- Panel Derecho: Cliente, Puntos y Total a Pagar ---
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.right_panel.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        self.setup_checkout_panel()

    def setup_product_selector(self):
        """Barra para buscar y agregar medicamentos al carrito."""
        selector_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        selector_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.entry_prod_search = ctk.CTkEntry(selector_frame, placeholder_text="Buscar medicamento por nombre...", width=280, height=38)
        self.entry_prod_search.pack(side="left", padx=(0, 10))

        self.btn_add_prod = ctk.CTkButton(selector_frame, text="Agregar al Carrito", width=130, height=38, fg_color="#2980B9", command=self.add_to_cart)
        self.btn_add_prod.pack(side="left")

    def setup_cart_table(self):
        """Tabla del carrito de compras (Detalle de Venta)."""
        cart_container = ctk.CTkFrame(self.left_panel)
        cart_container.grid(row=1, column=0, sticky="nsew")
        cart_container.grid_rowconfigure(0, weight=1)
        cart_container.grid_columnconfigure(0, weight=1)

        columns = ("ID", "Medicamento", "Cant", "P. Unitario", "Subtotal")
        self.tree_cart = ttk.Treeview(cart_container, columns=columns, show="headings", height=12)
        
        widths = [40, 180, 60, 90, 90]
        for col, w in zip(columns, widths):
            self.tree_cart.heading(col, text=col)
            self.tree_cart.column(col, width=w, anchor="center")

        self.tree_cart.pack(fill="both", expand=True, padx=10, pady=10)

        # Datos de prueba en carrito
        self.tree_cart.insert("", "end", values=(1, "Paracetamol 500mg", 2, "$45.50", "$91.00"))

    def setup_checkout_panel(self):
        """Panel derecho para asociar cliente por RFC, ver puntos y finalizar venta."""
        lbl_checkout = ctk.CTkLabel(self.right_panel, text="Resumen de Venta", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_checkout.pack(padx=20, pady=(20, 15), anchor="w")

        # Búsqueda de Cliente por RFC
        self.entry_rfc_client = ctk.CTkEntry(self.right_panel, placeholder_text="RFC del Cliente", width=260, height=38)
        self.entry_rfc_client.pack(padx=20, pady=8)

        self.btn_search_client = ctk.CTkButton(self.right_panel, text="Verificar Cliente / Puntos", width=260, height=35, fg_color="#8E44AD", command=self.verify_client)
        self.btn_search_client.pack(padx=20, pady=8)

        # Indicador de Puntos Acumulados y Descuentos
        self.lbl_points_info = ctk.CTkLabel(self.right_panel, text="Puntos acumulados: 40 pts\n(Faltan 10 pts para 10% de descuento)", font=ctk.CTkFont(size=12), text_color="#F39C12", justify="left")
        self.lbl_points_info.pack(padx=20, pady=10, anchor="w")

        # Separador / Totales
        self.lbl_subtotal = ctk.CTkLabel(self.right_panel, text="Subtotal: $91.00", font=ctk.CTkFont(size=14))
        self.lbl_subtotal.pack(padx=20, pady=5, anchor="w")

        self.lbl_descuento = ctk.CTkLabel(self.right_panel, text="Descuento aplicado: $0.00", font=ctk.CTkFont(size=14), text_color="#27AE60")
        self.lbl_descuento.pack(padx=20, pady=5, anchor="w")

        self.lbl_total = ctk.CTkLabel(self.right_panel, text="TOTAL: $91.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_total.pack(padx=20, pady=(10, 20), anchor="w")

        # Botón Finalizar Venta (Resta stock, acumula puntos y genera factura PDF)
        self.btn_finish_sale = ctk.CTkButton(
            self.right_panel, text="Completar Venta y Facturar", fg_color="#27AE60", hover_color="#219653",
            command=self.complete_sale, width=260, height=45
        )
        self.btn_finish_sale.pack(padx=20, pady=(10, 20))

    def add_to_cart(self):
        messagebox.showinfo("Carrito", "Medicamento agregado al carrito de compras.")

    def verify_client(self):
        rfc = self.entry_rfc_client.get().strip()
        if not rfc:
            messagebox.showerror("Error", "Ingrese un RFC para consultar los puntos.")
            return
        messagebox.showinfo("Cliente Encontrado", f"Cliente con RFC {rfc} verificado exitosamente.")

    def complete_sale(self):
        messagebox.showinfo("Venta Exitosa", "Venta registrada con éxito.\n- Stock actualizado.\n- Puntos actualizados.\n- Factura generada y enviada por correo.")