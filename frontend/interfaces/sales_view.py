import customtkinter as ctk
from tkinter import messagebox, ttk
from backend.services.product_service import get_all_products
from backend.services.sale_service import (
    get_client_by_rfc,
    validate_cart_restrictions,
    calculate_sale_summary,
    process_sale
)

class SalesView(ctk.CTkFrame):
    """
    Modulo de Punto de Venta (POS) de Farmacia CUCEI.
    Implementa:
    - Carrito interactivo con validacion de stock real.
    - Restriccion estricta de prohibicion de venta simultanea de alcohol y medicamentos controlados.
    - Busqueda de cliente por RFC obligatoria.
    - Programa de puntos: 10% de descuento automatico al acumular 50 puntos o mas.
    - Asignacion de +10 puntos si el total de compra supera $500.00 MXN.
    - Metodos de pago: Efectivo con calculo de cambio y Tarjeta.
    - Checkbox de requerimiento de factura.
    """
    def __init__(self, parent, role="Encargado", user_id=None):
        super().__init__(parent, fg_color="transparent")
        self.role = role
        self.user_id = user_id

        # Estado interno de la transaccion
        self.cart_items = []
        self.products_cache = []
        self.current_client = None

        # Configuracion del grid principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Titulo del modulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Punto de Venta (POS) - Farmacia CUCEI", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # 2. Contenedor principal dividido (Izquierda: Carrito / Derecha: Checkout)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=3)
        self.main_container.grid_columnconfigure(1, weight=2)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Buscador y Carrito
        self.left_panel = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.setup_product_selector()
        self.setup_cart_table()

        # Panel Derecho: Cliente, Puntos y Checkout
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.right_panel.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        self.setup_checkout_panel()

        # Cargar catalogo inicial
        self.load_products_catalog()

    # =========================================================================
    # PANEL IZQUIERDO: SELECCIÓN Y CARRITO
    # =========================================================================
    def setup_product_selector(self):
        """Barra interactiva para seleccionar producto y agregar al carrito."""
        selector_frame = ctk.CTkFrame(self.left_panel, corner_radius=8)
        selector_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=0)

        lbl_top = ctk.CTkLabel(selector_frame, text="Seleccion de Productos", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_top.grid(row=0, column=0, columnspan=3, padx=12, pady=(10, 4), sticky="w")

        self.combo_products = ctk.CTkComboBox(
            selector_frame, 
            width=360, 
            height=35, 
            command=self.on_product_chosen
        )
        self.combo_products.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="w")

        self.entry_prod_cant = ctk.CTkEntry(
            selector_frame, 
            placeholder_text="Cant.", 
            width=70, 
            height=35
        )
        self.entry_prod_cant.grid(row=1, column=1, padx=(0, 8), pady=(0, 8))
        self.entry_prod_cant.insert(0, "1")

        self.btn_add_prod = ctk.CTkButton(
            selector_frame, 
            text="Agregar al Carrito", 
            width=140, 
            height=35, 
            fg_color="#2980B9", 
            hover_color="#2471A3",
            command=self.add_to_cart,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.btn_add_prod.grid(row=1, column=2, padx=(0, 12), pady=(0, 8))

        self.lbl_prod_info = ctk.CTkLabel(
            selector_frame, 
            text="Stock disponible: - | Precio: - | Clasificacion: -", 
            font=ctk.CTkFont(size=11), 
            text_color="gray"
        )
        self.lbl_prod_info.grid(row=2, column=0, columnspan=3, padx=12, pady=(0, 8), sticky="w")

    def setup_cart_table(self):
        """Tabla que muestra los productos en el carrito."""
        cart_container = ctk.CTkFrame(self.left_panel)
        cart_container.grid(row=1, column=0, sticky="nsew")
        cart_container.grid_rowconfigure(0, weight=1)
        cart_container.grid_columnconfigure(0, weight=1)

        columns = ("ID", "Folio", "Producto", "Cant", "P. Unitario", "Subtotal", "Tipo")
        self.tree_cart = ttk.Treeview(cart_container, columns=columns, show="headings", height=12)
        
        widths = [40, 75, 170, 50, 75, 75, 80]
        for col, w in zip(columns, widths):
            self.tree_cart.heading(col, text=col)
            self.tree_cart.column(col, width=w, anchor="center")

        self.tree_cart.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Barra de botones bajo la tabla
        cart_bar = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        cart_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        btn_remove = ctk.CTkButton(
            cart_bar, 
            text="Quitar Producto", 
            fg_color="#7F8C8D", 
            hover_color="#626567",
            command=self.remove_from_cart, 
            width=140, 
            height=32
        )
        btn_remove.pack(side="left")

        btn_clear = ctk.CTkButton(
            cart_bar, 
            text="Vaciar Carrito", 
            fg_color="#C0392B", 
            hover_color="#962D22",
            command=self.clear_cart, 
            width=120, 
            height=32
        )
        btn_clear.pack(side="left", padx=10)

    # =========================================================================
    # PANEL DERECHO: CLIENTE, TOTALES Y CHECKOUT
    # =========================================================================
    def setup_checkout_panel(self):
        """Configura la seccion de cliente, lealtad, metodo de pago y cobro."""
        # Scrollable container para evitar desbordes en resoluciones pequeñas
        scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_checkout = ctk.CTkLabel(scroll, text="Resumen de Venta y Pago", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_checkout.pack(anchor="w", pady=(0, 10))

        # 1. Asociacion de Cliente por RFC (Obligatorio)
        lbl_cli_sec = ctk.CTkLabel(scroll, text="Cliente (RFC Obligatorio):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_cli_sec.pack(anchor="w", pady=(5, 2))

        rfc_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        rfc_bar.pack(fill="x", pady=(0, 5))

        self.entry_rfc_client = ctk.CTkEntry(rfc_bar, placeholder_text="RFC del Cliente", height=35)
        self.entry_rfc_client.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_rfc_client.bind("<Return>", lambda event: self.verify_client())

        self.btn_search_client = ctk.CTkButton(
            rfc_bar, 
            text="Verificar", 
            width=80, 
            height=35, 
            fg_color="#8E44AD", 
            hover_color="#732D91",
            command=self.verify_client
        )
        self.btn_search_client.pack(side="right")

        self.lbl_client_info = ctk.CTkLabel(
            scroll, 
            text="Ningun cliente asociado todavia.", 
            font=ctk.CTkFont(size=11), 
            text_color="gray", 
            justify="left",
            wraplength=260
        )
        self.lbl_client_info.pack(anchor="w", pady=(2, 6))

        # Indicador de Puntos y Lealtad
        self.lbl_points_info = ctk.CTkLabel(
            scroll, 
            text="Puntos acumulados: 0 pts", 
            font=ctk.CTkFont(size=12), 
            text_color="#F39C12", 
            justify="left",
            wraplength=260
        )
        self.lbl_points_info.pack(anchor="w", pady=(0, 10))

        # Separador visual
        sep = ctk.CTkFrame(scroll, height=2, fg_color="gray30")
        sep.pack(fill="x", pady=6)

        # 2. Desglose de Totales
        self.lbl_subtotal = ctk.CTkLabel(scroll, text="Subtotal: $0.00", font=ctk.CTkFont(size=13))
        self.lbl_subtotal.pack(anchor="w", pady=2)

        self.lbl_descuento = ctk.CTkLabel(scroll, text="Descuento (10%): $0.00", font=ctk.CTkFont(size=13), text_color="#27AE60")
        self.lbl_descuento.pack(anchor="w", pady=2)

        self.lbl_total = ctk.CTkLabel(scroll, text="TOTAL: $0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_total.pack(anchor="w", pady=(6, 12))

        # 3. Metodo de Pago
        lbl_pago = ctk.CTkLabel(scroll, text="Metodo de Pago:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_pago.pack(anchor="w", pady=(4, 2))

        self.combo_metodo_pago = ctk.CTkComboBox(
            scroll, 
            values=["Efectivo", "Tarjeta"], 
            height=35,
            command=self.on_payment_method_change
        )
        self.combo_metodo_pago.pack(fill="x", pady=(0, 8))
        self.combo_metodo_pago.set("Efectivo")

        self.entry_efectivo = ctk.CTkEntry(scroll, placeholder_text="Efectivo recibido ($)", height=35)
        self.entry_efectivo.pack(fill="x", pady=(0, 6))
        self.entry_efectivo.bind("<KeyRelease>", lambda event: self.calculate_change())

        self.lbl_cambio = ctk.CTkLabel(scroll, text="Cambio a entregar: $0.00", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_cambio.pack(anchor="w", pady=(0, 10))

        # 4. Checkbox Factura
        self.var_factura = ctk.BooleanVar(value=False)
        self.chk_factura = ctk.CTkCheckBox(
            scroll, 
            text="¿Requiere Factura? (Enviar PDF a correo)", 
            variable=self.var_factura,
            font=ctk.CTkFont(size=11)
        )
        self.chk_factura.pack(anchor="w", pady=(4, 15))

        # 5. Boton Finalizar Venta
        self.btn_finish_sale = ctk.CTkButton(
            scroll, 
            text="Completar Venta", 
            fg_color="#27AE60", 
            hover_color="#219653",
            command=self.complete_sale, 
            height=42,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_finish_sale.pack(fill="x", pady=(5, 10))

    # =========================================================================
    # LÓGICA DE CATÁLOGO Y CARRITO
    # =========================================================================
    def load_products_catalog(self):
        """Consulta el inventario de la base de datos para el selector."""
        self.products_cache = get_all_products()
        if not self.products_cache:
            self.combo_products.configure(values=["Sin productos en inventario"])
            self.combo_products.set("Sin productos en inventario")
            return

        values = [f"{p['id_producto']} - {p['nombre']} ({p['folio']})" for p in self.products_cache]
        self.combo_products.configure(values=values)
        self.combo_products.set(values[0])
        self.on_product_chosen(values[0])

    def on_product_chosen(self, choice):
        """Muestra datos del producto seleccionado (stock, precio, controlado/alcohol)."""
        try:
            prod_id = int(choice.split(" - ")[0])
            prod = next((p for p in self.products_cache if p["id_producto"] == prod_id), None)
            if prod:
                tags = []
                if prod["es_controlado"]:
                    tags.append("Controlado")
                if prod["es_alcohol"]:
                    tags.append("Alcohol")
                tipo_str = ", ".join(tags) if tags else "General"

                self.lbl_prod_info.configure(
                    text=f"Stock disp: {prod['stock']} uds. | Precio: ${prod['precio_venta']:.2f} | Tipo: {tipo_str}"
                )
        except Exception:
            pass

    def add_to_cart(self):
        """Agrega un producto validando disponibilidad de stock."""
        choice = self.combo_products.get()
        if not choice or "Sin productos" in choice:
            messagebox.showerror("Error", "Seleccione un producto valido.")
            return

        try:
            prod_id = int(choice.split(" - ")[0])
            cant = int(self.entry_prod_cant.get().strip())
            if cant <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Dato invalido", "La cantidad debe ser un numero entero mayor a 0.")
            return

        prod = next((p for p in self.products_cache if p["id_producto"] == prod_id), None)
        if not prod:
            return

        # Validar stock disponible
        cant_actual_carrito = sum(item["cantidad"] for item in self.cart_items if item["id_producto"] == prod_id)
        if (cant_actual_carrito + cant) > prod["stock"]:
            messagebox.showerror(
                "Stock Insuficiente", 
                f"No hay suficiente inventario para '{prod['nombre']}'.\nStock actual en BD: {prod['stock']} uds.\nEn carrito: {cant_actual_carrito} uds."
            )
            return

        # Determinar tipo para despliegue
        tipo = "Normal"
        if prod["es_controlado"] and prod["es_alcohol"]:
            tipo = "Ctrl/Alc"
        elif prod["es_controlado"]:
            tipo = "Controlado"
        elif prod["es_alcohol"]:
            tipo = "Alcohol"

        existing = next((item for item in self.cart_items if item["id_producto"] == prod_id), None)
        if existing:
            existing["cantidad"] += cant
            existing["subtotal"] = round(existing["cantidad"] * prod["precio_venta"], 2)
        else:
            self.cart_items.append({
                "id_producto": prod["id_producto"],
                "folio": prod["folio"],
                "nombre": prod["nombre"],
                "cantidad": cant,
                "precio_unitario": prod["precio_venta"],
                "subtotal": round(cant * prod["precio_venta"], 2),
                "es_controlado": prod["es_controlado"],
                "es_alcohol": prod["es_alcohol"],
                "tipo_display": tipo
            })

        self.refresh_cart_display()

    def remove_from_cart(self):
        """Retira el producto seleccionado del carrito."""
        selected = self.tree_cart.selection()
        if not selected:
            messagebox.showwarning("Seleccion", "Seleccione un producto del carrito para retirarlo.")
            return

        item_vals = self.tree_cart.item(selected[0], "values")
        prod_id = int(item_vals[0])
        self.cart_items = [item for item in self.cart_items if item["id_producto"] != prod_id]
        self.refresh_cart_display()

    def clear_cart(self):
        """Vacia el carrito por completo."""
        self.cart_items.clear()
        self.refresh_cart_display()

    def refresh_cart_display(self):
        """Actualiza la tabla del carrito y recalcula los totales."""
        for item in self.tree_cart.get_children():
            self.tree_cart.delete(item)

        for p in self.cart_items:
            self.tree_cart.insert("", "end", values=(
                p["id_producto"],
                p["folio"],
                p["nombre"],
                p["cantidad"],
                f"${p['precio_unitario']:.2f}",
                f"${p['subtotal']:,.2f}",
                p["tipo_display"]
            ))

        self.update_totals_display()

    # =========================================================================
    # LÓGICA DE LEALTAD, TOTALES Y COBRO
    # =========================================================================
    def verify_client(self):
        """Consulta el cliente en la base de datos a traves de su RFC."""
        rfc = self.entry_rfc_client.get().strip()
        if not rfc:
            messagebox.showerror("Error", "Ingrese el RFC del cliente para verificar.")
            return

        client = get_client_by_rfc(rfc)
        if client:
            self.current_client = client
            pts = client["puntos_acumulados"]
            self.lbl_client_info.configure(
                text=f"Cliente: {client['nombre']}\nRFC: {client['rfc']} | Ciudad: {client['ciudad']}",
                text_color="white"
            )
            
            if pts >= 50:
                self.lbl_points_info.configure(
                    text=f"Puntos acumulados: {pts} pts\nAplica 10% de descuento por programa de lealtad.",
                    text_color="#2ECC71"
                )
            else:
                faltan = 50 - pts
                self.lbl_points_info.configure(
                    text=f"Puntos acumulados: {pts} pts\nFaltan {faltan} pts para obtener 10% de descuento.",
                    text_color="#F39C12"
                )
            self.update_totals_display()
        else:
            self.current_client = None
            self.lbl_client_info.configure(text="Cliente no encontrado con ese RFC.", text_color="#E74C3C")
            self.lbl_points_info.configure(text="Puntos acumulados: 0 pts", text_color="gray")
            self.update_totals_display()
            messagebox.showwarning("No encontrado", f"No existe ningun cliente con el RFC '{rfc}'. Registre al cliente en el modulo de Clientes primero.")

    def update_totals_display(self):
        """Recalcula subtotales, descuentos y total a pagar en tiempo real."""
        client_pts = self.current_client["puntos_acumulados"] if self.current_client else 0
        summary = calculate_sale_summary(self.cart_items, client_pts)

        self.lbl_subtotal.configure(text=f"Subtotal: ${summary['subtotal']:,.2f}")
        if summary["aplica_descuento"]:
            self.lbl_descuento.configure(text=f"Descuento (10%): -${summary['monto_descuento']:,.2f}")
        else:
            self.lbl_descuento.configure(text="Descuento (10%): $0.00")

        self.lbl_total.configure(text=f"TOTAL: ${summary['total']:,.2f}")
        self.calculate_change()

    def on_payment_method_change(self, choice):
        """Ajusta los campos segun el metodo de pago seleccionado."""
        if choice == "Tarjeta":
            self.entry_efectivo.delete(0, 'end')
            self.entry_efectivo.configure(state="disabled")
            self.lbl_cambio.configure(text="Pago con tarjeta bancaria")
        else:
            self.entry_efectivo.configure(state="normal")
            self.calculate_change()

    def calculate_change(self):
        """Calcula el cambio cuando el pago es en efectivo."""
        if self.combo_metodo_pago.get() != "Efectivo":
            return

        client_pts = self.current_client["puntos_acumulados"] if self.current_client else 0
        summary = calculate_sale_summary(self.cart_items, client_pts)
        total = summary["total"]

        val_str = self.entry_efectivo.get().strip()
        if not val_str:
            self.lbl_cambio.configure(text="Cambio a entregar: $0.00")
            return

        try:
            efectivo = float(val_str)
            if efectivo >= total:
                cambio = efectivo - total
                self.lbl_cambio.configure(text=f"Cambio a entregar: ${cambio:,.2f} MXN", text_color="#2ECC71")
            else:
                faltante = total - efectivo
                self.lbl_cambio.configure(text=f"Faltan: ${faltante:,.2f} MXN", text_color="#E74C3C")
        except ValueError:
            self.lbl_cambio.configure(text="Monto invalido", text_color="#E74C3C")

    def complete_sale(self):
        """Valida y procesa la venta en la base de datos."""
        if not self.cart_items:
            messagebox.showwarning("Carrito Vacio", "Agregue al menos un producto al carrito de compras.")
            return

        if not self.current_client:
            messagebox.showerror("Cliente Requerido", "Es obligatorio ingresar y verificar el RFC de un cliente registrado.")
            return

        # Validacion estricta de alcohol + medicamento controlado
        es_valido, msg_restr = validate_cart_restrictions(self.cart_items)
        if not es_valido:
            messagebox.showerror("Venta Bloqueada por Restriccion Legal", msg_restr)
            return

        metodo = self.combo_metodo_pago.get()
        efectivo_val = 0.0

        client_pts = self.current_client["puntos_acumulados"]
        summary = calculate_sale_summary(self.cart_items, client_pts)
        total = summary["total"]

        if metodo == "Efectivo":
            try:
                efectivo_val = float(self.entry_efectivo.get().strip())
                if efectivo_val < total:
                    messagebox.showerror("Efectivo Insuficiente", f"El monto en efectivo ingresado no cubre el total de ${total:,.2f} MXN.")
                    return
            except ValueError:
                messagebox.showerror("Dato Invalido", "Ingrese un monto numerico valido en el campo de efectivo.")
                return

        req_factura = self.var_factura.get()

        # Confirmacion final
        if not messagebox.askyesno("Confirmar Cobro", f"¿Desea confirmar la venta por un total de ${total:,.2f} MXN ({metodo})?"):
            return

        success, msg, id_venta, res = process_sale(
            cart_items=self.cart_items,
            id_cliente=self.current_client["id_cliente"],
            id_usuario=self.user_id,
            metodo_pago=metodo,
            efectivo_recibido=efectivo_val,
            requiere_factura=req_factura
        )

        if success:
            if req_factura:
                msg += "\n\n(Factura solicitada: Se generara y enviara en el modulo de Facturacion)."

            messagebox.showinfo("Venta Finalizada con Exito", msg)

            # Limpiar estado
            self.cart_items.clear()
            self.refresh_cart_display()
            self.current_client = None
            self.entry_rfc_client.delete(0, 'end')
            self.entry_efectivo.delete(0, 'end')
            self.lbl_client_info.configure(text="Ningun cliente asociado todavia.", text_color="gray")
            self.lbl_points_info.configure(text="Puntos acumulados: 0 pts", text_color="#F39C12")
            self.load_products_catalog()
        else:
            messagebox.showerror("Error al Procesar Venta", msg)

if __name__ == "__main__":
    # Prueba unitaria individual del Punto de Venta (POS)
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

    app = ctk.CTk()
    app.title("Prueba Unitaria - Punto de Venta (POS)")
    app.geometry("1100x650")

    view = SalesView(parent=app, role="Encargado")
    view.pack(fill="both", expand=True)

    app.mainloop()
