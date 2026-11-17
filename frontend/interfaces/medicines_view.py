import customtkinter as ctk
from tkinter import messagebox, ttk
from backend.services.product_service import (
    get_all_products,
    search_products,
    create_product,
    delete_product
)

class MedicinesView(ctk.CTkFrame):
    """
    Vista para el catalogo e inventario general de la farmacia.
    Permite administrar medicamentos, bebidas, despensa y productos generales.
    """
    def __init__(self, parent, role="Admin"):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuracion de reticula principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Titulo del modulo
        title_text = "Catalogo y Gestion de Productos" if self.role in ["Admin", "Gerente"] else "Busqueda y Consulta de Productos"
        self.title_label = ctk.CTkLabel(
            self, 
            text=title_text, 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Panel izquierdo para formulario (Solo Admin y Gerente)
        if self.role in ["Admin", "Gerente"]:
            self.form_frame = ctk.CTkFrame(self.main_container, width=320, corner_radius=10)
            self.form_frame.grid(row=0, column=0, padx=(0, 15), pady=0, sticky="nsew")
            self.setup_form()
            table_col = 1
        else:
            table_col = 0

        # Panel derecho para busqueda y tabla
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="transparent")
        self.right_panel.grid(row=0, column=table_col, padx=0, pady=0, sticky="nsew")
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.setup_search_bar()
        self.setup_table()

    def setup_form(self):
        """Configura el formulario de registro de productos para Admin y Gerente."""
        lbl_form = ctk.CTkLabel(self.form_frame, text="Gestion de Producto", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_form.pack(padx=20, pady=(15, 10), anchor="w")

        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Nombre del producto", width=260, height=35)
        self.entry_nombre.pack(padx=20, pady=5)

        self.entry_folio = ctk.CTkEntry(self.form_frame, placeholder_text="Folio (Vacio para autogenerar)", width=260, height=35)
        self.entry_folio.pack(padx=20, pady=5)

        # Selector de categoria
        lbl_cat = ctk.CTkLabel(self.form_frame, text="Categoria:", font=ctk.CTkFont(size=12))
        lbl_cat.pack(padx=20, pady=(4, 2), anchor="w")

        categorias_base = ["Medicamento", "Despensa", "Bebidas", "Cuidado Personal", "Material de Curacion", "Otros"]
        self.combo_categoria = ctk.CTkComboBox(self.form_frame, values=categorias_base, width=260, height=35)
        self.combo_categoria.pack(padx=20, pady=(0, 5))
        self.combo_categoria.set("Medicamento")

        self.entry_pcompra = ctk.CTkEntry(self.form_frame, placeholder_text="Precio Compra ($)", width=260, height=35)
        self.entry_pcompra.pack(padx=20, pady=5)

        self.entry_pventa = ctk.CTkEntry(self.form_frame, placeholder_text="Precio Venta ($)", width=260, height=35)
        self.entry_pventa.pack(padx=20, pady=5)

        self.entry_stock = ctk.CTkEntry(self.form_frame, placeholder_text="Stock inicial", width=260, height=35)
        self.entry_stock.pack(padx=20, pady=5)

        # Banderas de control de venta
        self.var_controlado = ctk.BooleanVar(value=False)
        self.chk_controlado = ctk.CTkCheckBox(
            self.form_frame, 
            text="Medicamento Controlado", 
            variable=self.var_controlado,
            font=ctk.CTkFont(size=12)
        )
        self.chk_controlado.pack(padx=20, pady=6, anchor="w")

        self.var_alcohol = ctk.BooleanVar(value=False)
        self.chk_alcohol = ctk.CTkCheckBox(
            self.form_frame, 
            text="Producto Alcoholico", 
            variable=self.var_alcohol,
            font=ctk.CTkFont(size=12)
        )
        self.chk_alcohol.pack(padx=20, pady=6, anchor="w")

        # Boton Guardar
        self.btn_guardar = ctk.CTkButton(
            self.form_frame, 
            text="Guardar Producto", 
            fg_color="#27AE60", 
            hover_color="#219653",
            command=self.save_product, 
            width=260, 
            height=38,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_guardar.pack(padx=20, pady=(12, 15))

    def setup_search_bar(self):
        """Barra de busqueda por nombre, folio o categoria."""
        self.search_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.entry_search = ctk.CTkEntry(
            self.search_frame, 
            placeholder_text="Buscar producto por nombre, folio o categoria...", 
            width=360, 
            height=35
        )
        self.entry_search.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.entry_search.bind("<Return>", lambda event: self.search_product())

        self.btn_search = ctk.CTkButton(
            self.search_frame, 
            text="Buscar", 
            width=90, 
            height=35, 
            command=self.search_product
        )
        self.btn_search.pack(side="left", padx=(0, 5))

        self.btn_refresh = ctk.CTkButton(
            self.search_frame, 
            text="Actualizar", 
            width=90, 
            height=35, 
            fg_color="#5D6D7E",
            command=lambda: self.load_products_from_db()
        )
        self.btn_refresh.pack(side="left", padx=(0, 5))

        if self.role in ["Admin", "Gerente"]:
            self.btn_delete = ctk.CTkButton(
                self.search_frame, 
                text="Eliminar", 
                width=90, 
                height=35, 
                fg_color="#C0392B", 
                hover_color="#962D22",
                command=self.delete_selected_product
            )
            self.btn_delete.pack(side="left")

    def setup_table(self):
        """Tabla para mostrar el inventario de productos."""
        table_container = ctk.CTkFrame(self.right_panel)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        columns = ("ID", "Folio", "Nombre", "Categoria", "P. Compra", "P. Venta", "Stock", "Controlado", "Alcohol")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=15)
        
        widths = [45, 85, 170, 110, 80, 80, 60, 85, 75]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Cargar los datos desde PostgreSQL
        self.load_products_from_db()

    def load_products_from_db(self, products=None):
        """Carga y muestra los productos reales de la base de datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if products is None:
            products = get_all_products()

        for p in products:
            es_ctrl = "Si" if p["es_controlado"] else "No"
            es_alc = "Si" if p["es_alcohol"] else "No"
            self.tree.insert("", "end", values=(
                p["id_producto"],
                p["folio"],
                p["nombre"],
                p["categoria"],
                f"${p['precio_compra']:.2f}",
                f"${p['precio_venta']:.2f}",
                p["stock"],
                es_ctrl,
                es_alc
            ))

    def save_product(self):
        """Valida y envia los datos para registrar un producto."""
        nombre = self.entry_nombre.get().strip()
        folio = self.entry_folio.get().strip()
        categoria = self.combo_categoria.get().strip()
        p_compra = self.entry_pcompra.get().strip()
        p_venta = self.entry_pventa.get().strip()
        stock = self.entry_stock.get().strip()
        es_ctrl = self.var_controlado.get()
        es_alc = self.var_alcohol.get()

        if not nombre:
            messagebox.showerror("Campo requerido", "El nombre del producto es obligatorio.")
            return

        try:
            pc_val = float(p_compra)
            pv_val = float(p_venta)
            stock_val = int(stock)
        except ValueError:
            messagebox.showerror("Dato invalido", "Los precios y el stock deben ser numericos.")
            return

        success, msg = create_product(
            nombre=nombre,
            categoria=categoria,
            precio_compra=pc_val,
            precio_venta=pv_val,
            stock=stock_val,
            es_controlado=es_ctrl,
            es_alcohol=es_alc,
            folio=folio if folio else None,
            creator_role=self.role
        )

        if success:
            messagebox.showinfo("Exito", msg)
            self.clear_form()
            self.load_products_from_db()
        else:
            messagebox.showerror("Error al guardar", msg)

    def search_product(self):
        """Filtra los productos por el texto ingresado."""
        query = self.entry_search.get().strip()
        if not query:
            self.load_products_from_db()
            return

        results = search_products(query)
        self.load_products_from_db(results)

    def delete_selected_product(self):
        """Elimina el producto seleccionado en la tabla."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccion requerida", "Seleccione un producto de la tabla para eliminarlo.")
            return

        item = self.tree.item(selected[0], "values")
        id_prod = int(item[0])
        nombre_prod = item[2]

        if not messagebox.askyesno("Confirmar Eliminacion", f"Desea eliminar el producto '{nombre_prod}'?"):
            return

        success, msg = delete_product(id_prod, creator_role=self.role)
        if success:
            messagebox.showinfo("Eliminado", msg)
            self.load_products_from_db()
        else:
            messagebox.showerror("Error", msg)

    def clear_form(self):
        """Limpia los campos del formulario."""
        self.entry_nombre.delete(0, 'end')
        self.entry_folio.delete(0, 'end')
        self.entry_pcompra.delete(0, 'end')
        self.entry_pventa.delete(0, 'end')
        self.entry_stock.delete(0, 'end')
        self.var_controlado.set(False)
        self.var_alcohol.set(False)

if __name__ == "__main__":
    # Prueba unitaria individual de la vista de Productos
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

    app = ctk.CTk()
    app.title("Prueba Unitaria - Catalogo de Productos")
    app.geometry("1080x620")

    # Puedes cambiar role="Admin", "Gerente" o "Encargado" para validar permisos
    view = MedicinesView(parent=app, role="Admin")
    view.pack(fill="both", expand=True)

    app.mainloop()
