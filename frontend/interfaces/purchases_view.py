import customtkinter as ctk
from tkinter import messagebox, ttk
from backend.services.product_service import get_all_products
from backend.services.purchase_service import (
    create_restock_orders,
    get_pending_purchases,
    get_purchase_details,
    receive_purchase
)
from backend.services.connectivity_service import check_internet_connection

class PurchasesView(ctk.CTkFrame):
    """
    Vista de compras a proveedores y control de restock.
    Implementa el flujo en dos fases:
    1. Solicitud de Restock con agrupacion automatica por proveedor (Estado: 'Enviado').
    2. Recepcion de pedidos pendientes para marcar como 'Surtido' e incrementar el stock real.
    """
    def __init__(self, parent, role="Gerente", user_id=None):
        super().__init__(parent, fg_color="transparent")
        self.role = role
        self.user_id = user_id

        # Lista temporal para armar el pedido de restock en la pestaña 1
        self.cart_items = []
        self.products_cache = []

        # Configuracion principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Titulo del modulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Compras a Proveedores y Reabastecimiento de Inventario", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # 2. Tabview para las dos fases
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.tab_solicitud = self.tabview.add("Solicitar Restock")
        self.tab_recepcion = self.tabview.add("Recepcion de Pedidos Pendientes")

        self.setup_tab_solicitud()
        self.setup_tab_recepcion()

        # Cargar datos iniciales
        self.load_products_for_selector()
        self.load_pending_purchases_table()

    # =========================================================================
    # PESTAÑA 1: SOLICITUD DE RESTOCK (AGRUPACIÓN AUTOMÁTICA)
    # =========================================================================
    def setup_tab_solicitud(self):
        """Configura el panel para seleccionar productos y generar ordenes de compra."""
        self.tab_solicitud.grid_columnconfigure(1, weight=1)
        self.tab_solicitud.grid_rowconfigure(0, weight=1)

        # Panel izquierdo: Formulario para añadir al carrito de restock
        left_panel = ctk.CTkFrame(self.tab_solicitud, width=320, corner_radius=10)
        left_panel.grid(row=0, column=0, padx=(0, 15), pady=10, sticky="nsew")

        lbl_sec = ctk.CTkLabel(left_panel, text="Agregar a Lista de Restock", font=ctk.CTkFont(size=15, weight="bold"))
        lbl_sec.pack(padx=15, pady=(15, 10), anchor="w")

        lbl_prod = ctk.CTkLabel(left_panel, text="Seleccionar Producto:", font=ctk.CTkFont(size=12))
        lbl_prod.pack(padx=15, pady=(5, 2), anchor="w")

        self.combo_products = ctk.CTkComboBox(left_panel, width=280, height=35, command=self.on_product_selected)
        self.combo_products.pack(padx=15, pady=(0, 10))

        self.lbl_current_stock = ctk.CTkLabel(left_panel, text="Stock actual: - | Proveedor: -", font=ctk.CTkFont(size=11), text_color="gray")
        self.lbl_current_stock.pack(padx=15, pady=(0, 10), anchor="w")

        self.entry_restock_cant = ctk.CTkEntry(left_panel, placeholder_text="Cantidad a solicitar", width=280, height=35)
        self.entry_restock_cant.pack(padx=15, pady=8)

        self.entry_restock_price = ctk.CTkEntry(left_panel, placeholder_text="Precio Compra Unitario ($)", width=280, height=35)
        self.entry_restock_price.pack(padx=15, pady=8)

        self.btn_add_to_restock = ctk.CTkButton(
            left_panel, 
            text="Agregar a la Lista", 
            fg_color="#2980B9", 
            hover_color="#2471A3",
            command=self.add_item_to_restock_cart, 
            width=280, 
            height=38,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_add_to_restock.pack(padx=15, pady=(15, 10))

        # Panel derecho: Tabla con la lista acumulada de restock y total
        right_panel = ctk.CTkFrame(self.tab_solicitud, corner_radius=10, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", pady=10)
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        table_card = ctk.CTkFrame(right_panel)
        table_card.grid(row=0, column=0, sticky="nsew")
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        columns = ("ID", "Folio", "Producto", "Proveedor", "Cant", "P. Compra", "Subtotal")
        self.tree_restock = ttk.Treeview(table_card, columns=columns, show="headings", height=12)
        
        widths = [45, 80, 180, 140, 60, 85, 85]
        for col, w in zip(columns, widths):
            self.tree_restock.heading(col, text=col)
            self.tree_restock.column(col, width=w, anchor="center")

        self.tree_restock.pack(fill="both", expand=True, padx=10, pady=10)

        # Barra inferior de accion
        footer_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        footer_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.lbl_restock_total = ctk.CTkLabel(
            footer_frame, 
            text="Total Estimado: $0.00", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_restock_total.pack(side="left", padx=10)

        self.btn_remove_item = ctk.CTkButton(
            footer_frame,
            text="Quitar Seleccionado",
            fg_color="#7F8C8D",
            hover_color="#626567",
            command=self.remove_item_from_restock_cart,
            width=150,
            height=38
        )
        self.btn_remove_item.pack(side="left", padx=10)

        self.btn_submit_restock = ctk.CTkButton(
            footer_frame, 
            text="Solicitar Restock (Agrupar por Proveedor)", 
            fg_color="#27AE60", 
            hover_color="#219653",
            command=self.submit_restock_orders, 
            width=280, 
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_submit_restock.pack(side="right", padx=10)

    # =========================================================================
    # PESTAÑA 2: RECEPCIÓN FÍSICA DE MERCANCÍA (SUBIR STOCK)
    # =========================================================================
    def setup_tab_recepcion(self):
        """Configura el panel para revisar ordenes enviadas y marcarlas como recibidas."""
        self.tab_recepcion.grid_columnconfigure(0, weight=1)
        self.tab_recepcion.grid_columnconfigure(1, weight=1)
        self.tab_recepcion.grid_rowconfigure(1, weight=1)

        # Barra de herramientas superior
        top_bar = ctk.CTkFrame(self.tab_recepcion, fg_color="transparent")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))

        lbl_instruccion = ctk.CTkLabel(
            top_bar, 
            text="Seleccione una orden pendiente (Estado: Enviado) para ver sus detalles y registrar el ingreso al almacen:",
            font=ctk.CTkFont(size=13)
        )
        lbl_instruccion.pack(side="left")

        btn_refresh_pending = ctk.CTkButton(
            top_bar, 
            text="Actualizar Lista", 
            width=120, 
            height=32, 
            command=self.load_pending_purchases_table
        )
        btn_refresh_pending.pack(side="right")

        # Panel izquierdo: Tabla de ordenes pendientes
        left_box = ctk.CTkFrame(self.tab_recepcion)
        left_box.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_box.grid_rowconfigure(1, weight=1)
        left_box.grid_columnconfigure(0, weight=1)

        lbl_box1 = ctk.CTkLabel(left_box, text="Ordenes de Compra Pendientes", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_box1.grid(row=0, column=0, padx=10, pady=8, sticky="w")

        cols_pending = ("ID", "Proveedor", "Fecha", "Solicitante", "Total", "Estado")
        self.tree_pending = ttk.Treeview(left_box, columns=cols_pending, show="headings", height=10)
        
        widths_p = [45, 130, 120, 110, 80, 75]
        for c, w in zip(cols_pending, widths_p):
            self.tree_pending.heading(c, text=c)
            self.tree_pending.column(c, width=w, anchor="center")

        self.tree_pending.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.tree_pending.bind("<<TreeviewSelect>>", self.on_pending_purchase_selected)

        # Panel derecho: Desglose de la orden seleccionada y boton de recepcion
        right_box = ctk.CTkFrame(self.tab_recepcion)
        right_box.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        right_box.grid_rowconfigure(1, weight=1)
        right_box.grid_columnconfigure(0, weight=1)

        self.lbl_selected_order_title = ctk.CTkLabel(
            right_box, 
            text="Detalle de Mercancia a Recibir (Ninguna seleccionada)", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_selected_order_title.grid(row=0, column=0, padx=10, pady=8, sticky="w")

        cols_detail = ("Folio", "Producto", "Cant. Recibir", "P. Compra", "Subtotal", "Stock Actual")
        self.tree_details = ttk.Treeview(right_box, columns=cols_detail, show="headings", height=10)

        widths_d = [75, 150, 75, 75, 75, 75]
        for c, w in zip(cols_detail, widths_d):
            self.tree_details.heading(c, text=c)
            self.tree_details.column(c, width=w, anchor="center")

        self.tree_details.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Boton inferior para surtir orden
        self.btn_mark_received = ctk.CTkButton(
            right_box, 
            text="Marcar como Recibido e Incrementar Stock", 
            fg_color="#27AE60", 
            hover_color="#219653",
            command=self.mark_order_as_received, 
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_mark_received.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

    # =========================================================================
    # MÉTODOS DE LA PESTAÑA 1 (SOLICITUD)
    # =========================================================================
    def load_products_for_selector(self):
        """Carga el catalogo de productos en el combobox de seleccion."""
        self.products_cache = get_all_products()
        if not self.products_cache:
            self.combo_products.configure(values=["No hay productos registrados"])
            self.combo_products.set("No hay productos registrados")
            return

        display_values = [f"{p['id_producto']} - {p['nombre']} ({p['folio']})" for p in self.products_cache]
        self.combo_products.configure(values=display_values)
        self.combo_products.set(display_values[0])
        self.on_product_selected(display_values[0])

    def on_product_selected(self, choice):
        """Al elegir un producto, precarga su stock actual y precio de compra."""
        try:
            prod_id = int(choice.split(" - ")[0])
            for p in self.products_cache:
                if p["id_producto"] == prod_id:
                    self.lbl_current_stock.configure(
                        text=f"Stock actual: {p['stock']} uds. | Proveedor: {p['proveedor_nombre']}"
                    )
                    self.entry_restock_price.delete(0, 'end')
                    self.entry_restock_price.insert(0, f"{p['precio_compra']:.2f}")
                    break
        except Exception:
            pass

    def add_item_to_restock_cart(self):
        """Agrega un producto a la lista temporal de restock."""
        choice = self.combo_products.get()
        if not choice or "No hay productos" in choice:
            messagebox.showerror("Error", "Seleccione un producto valido.")
            return

        cant_str = self.entry_restock_cant.get().strip()
        price_str = self.entry_restock_price.get().strip()

        if not cant_str or not price_str:
            messagebox.showerror("Campos requeridos", "Ingrese la cantidad y el precio de compra unitario.")
            return

        try:
            cant = int(cant_str)
            price = float(price_str)
            if cant <= 0 or price < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Dato invalido", "La cantidad debe ser un entero positivo y el precio numerico.")
            return

        prod_id = int(choice.split(" - ")[0])
        prod_obj = next((p for p in self.products_cache if p["id_producto"] == prod_id), None)
        if not prod_obj:
            return

        subtotal = round(cant * price, 2)

        # Si ya estaba en la lista, actualizar cantidad
        existing = next((item for item in self.cart_items if item["id_producto"] == prod_id), None)
        if existing:
            existing["cantidad"] += cant
            existing["precio_compra_unitario"] = price
            existing["subtotal"] = round(existing["cantidad"] * price, 2)
        else:
            self.cart_items.append({
                "id_producto": prod_id,
                "folio": prod_obj["folio"],
                "nombre": prod_obj["nombre"],
                "proveedor_nombre": prod_obj["proveedor_nombre"],
                "cantidad": cant,
                "precio_compra_unitario": price,
                "subtotal": subtotal
            })

        self.refresh_restock_table()
        self.entry_restock_cant.delete(0, 'end')

    def refresh_restock_table(self):
        """Actualiza la tabla y el total acumulado de restock."""
        for item in self.tree_restock.get_children():
            self.tree_restock.delete(item)

        total = 0.0
        for p in self.cart_items:
            total += p["subtotal"]
            self.tree_restock.insert("", "end", values=(
                p["id_producto"],
                p["folio"],
                p["nombre"],
                p["proveedor_nombre"],
                p["cantidad"],
                f"${p['precio_compra_unitario']:.2f}",
                f"${p['subtotal']:,.2f}"
            ))

        self.lbl_restock_total.configure(text=f"Total Estimado: ${total:,.2f}")

    def remove_item_from_restock_cart(self):
        """Quita un producto seleccionado de la lista temporal."""
        selected = self.tree_restock.selection()
        if not selected:
            messagebox.showwarning("Seleccion", "Seleccione un producto para retirarlo de la lista.")
            return

        item_vals = self.tree_restock.item(selected[0], "values")
        prod_id = int(item_vals[0])
        self.cart_items = [p for p in self.cart_items if p["id_producto"] != prod_id]
        self.refresh_restock_table()

    def submit_restock_orders(self):
        """Envia la solicitud de restock aplicando agrupacion automatica por proveedor."""
        # Verificacion obligatoria de conexion a internet
        if not check_internet_connection():
            messagebox.showerror(
                "Sin Conexion a Internet",
                "El sistema requiere conexion activa a internet para emitir ordenes de compra y notificar a proveedores."
            )
            return

        if not self.cart_items:
            messagebox.showwarning("Lista vacia", "Agregue al menos un producto a la orden de restock.")
            return

        if not messagebox.askyesno(
            "Confirmar Restock", 
            "El sistema agrupara automaticamente los productos seleccionados por proveedor y generara las ordenes en estado 'Enviado'.\n\n¿Desea continuar?"
        ):
            return

        success, msg, created_ids = create_restock_orders(
            items_list=self.cart_items,
            id_usuario=self.user_id,
            creator_role=self.role
        )

        if success:
            messagebox.showinfo("Restock Solicitado", msg)
            self.cart_items.clear()
            self.refresh_restock_table()
            self.load_pending_purchases_table()
            self.tabview.set("Recepcion de Pedidos Pendientes")
        else:
            messagebox.showerror("Error al procesar restock", msg)

    # =========================================================================
    # MÉTODOS DE LA PESTAÑA 2 (RECEPCIÓN Y ACTUALIZACIÓN DE STOCK)
    # =========================================================================
    def load_pending_purchases_table(self):
        """Consulta y despliega las ordenes en estado 'Enviado'."""
        for item in self.tree_pending.get_children():
            self.tree_pending.delete(item)

        for item in self.tree_details.get_children():
            self.tree_details.delete(item)

        self.lbl_selected_order_title.configure(text="Detalle de Mercancia a Recibir (Ninguna seleccionada)")

        pending = get_pending_purchases()
        for p in pending:
            self.tree_pending.insert("", "end", values=(
                p["id_compra"],
                p["proveedor_nombre"],
                p["fecha_hora"][:16],
                p["usuario_nombre"],
                f"${p['total_compra']:,.2f}",
                p["estado_pedido"]
            ))

    def on_pending_purchase_selected(self, event):
        """Al seleccionar una orden pendiente, carga sus detalles correspondientes."""
        selected = self.tree_pending.selection()
        if not selected:
            return

        values = self.tree_pending.item(selected[0], "values")
        id_compra = int(values[0])
        prov_nombre = values[1]

        self.lbl_selected_order_title.configure(
            text=f"Detalle de Orden #{id_compra} - Proveedor: {prov_nombre}"
        )

        for item in self.tree_details.get_children():
            self.tree_details.delete(item)

        details = get_purchase_details(id_compra)
        for d in details:
            self.tree_details.insert("", "end", values=(
                d["producto_folio"],
                d["producto_nombre"],
                d["cantidad"],
                f"${d['precio_compra_unitario']:.2f}",
                f"${d['subtotal']:,.2f}",
                f"{d['stock_actual']} uds."
            ))

    def mark_order_as_received(self):
        """Marca la orden seleccionada como surtida y suma las cantidades al inventario."""
        selected = self.tree_pending.selection()
        if not selected:
            messagebox.showwarning("Seleccion requerida", "Seleccione una orden pendiente para marcarla como recibida.")
            return

        values = self.tree_pending.item(selected[0], "values")
        id_compra = int(values[0])
        prov_nombre = values[1]

        if not messagebox.askyesno(
            "Confirmar Ingreso a Almacen",
            f"¿Confirma la recepcion fisica de la orden #{id_compra} ({prov_nombre})?\n\nAl confirmar, las cantidades se sumaran al stock real de la base de datos."
        ):
            return

        success, msg = receive_purchase(id_compra, creator_role=self.role)
        if success:
            messagebox.showinfo("Almacen Actualizado", msg)
            self.load_pending_purchases_table()
            self.load_products_for_selector()
        else:
            messagebox.showerror("Error", msg)

if __name__ == "__main__":
    # Prueba unitaria individual de la vista de Compras
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

    app = ctk.CTk()
    app.title("Prueba Unitaria - Compras y Restock")
    app.geometry("1100x650")

    view = PurchasesView(parent=app, role="Gerente")
    view.pack(fill="both", expand=True)

    app.mainloop()
