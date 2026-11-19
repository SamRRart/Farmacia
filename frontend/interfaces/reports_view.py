"""
Vista de Reportes Gerenciales del Sistema Farmacia CUCEI.
Conectada en tiempo real a la base de datos remota (Supabase/PostgreSQL)
a traves de report_service.py y GestorReportes.
Sin datos mock. Sin emojis.
"""

import customtkinter as ctk
from tkinter import messagebox, ttk

from backend.models.reports import GestorReportes
from backend.services.report_service import export_report_to_pdf
from backend.services.connectivity_service import check_internet_connection


class ReportsView(ctk.CTkFrame):
    """
    Modulo de Reportes Gerenciales.
    Genera y visualiza reportes dinamicos de:
      - Clientes por Ciudad / Estado
      - Ventas por Rango de Fechas
      - Compras por Rango de Fechas
      - Facturas con Mayores Ventas
    Permite exportar cualquier reporte activo a PDF con membrete institucional.
    """
    def __init__(self, parent, role):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Estado interno
        self._current_rows = []     # Lista de dicts retornados por report_service
        self._current_kpis = {}     # Resumen de KPIs del reporte activo
        self._current_headers = []  # Cabeceras de la tabla activa
        self._current_col_keys = []

        # Layout principal
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_title()
        self._build_filters_panel()
        self._build_kpis_panel()
        self._build_table_panel()

        # Cargar reporte inicial por defecto
        self.on_report_type_change("Clientes por Ciudad / Estado")

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------

    def _build_title(self):
        """Encabezado del modulo."""
        self.title_label = ctk.CTkLabel(
            self,
            text="Reportes Gerenciales del Sistema",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

    def _build_filters_panel(self):
        """Panel de filtros: tipo de reporte, parametros de busqueda y acciones."""
        filter_frame = ctk.CTkFrame(self, corner_radius=10)
        filter_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        filter_frame.grid_columnconfigure(6, weight=1)

        # Selector de tipo de reporte
        lbl_tipo = ctk.CTkLabel(
            filter_frame,
            text="Tipo de Reporte:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_tipo.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.combo_tipo_reporte = ctk.CTkComboBox(
            filter_frame,
            values=[
                "Clientes por Ciudad / Estado",
                "Ventas por Rango de Fechas",
                "Compras por Rango de Fechas",
                "Facturas con Mayores Ventas"
            ],
            width=265,
            height=35,
            command=self.on_report_type_change
        )
        self.combo_tipo_reporte.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        self.combo_tipo_reporte.set("Clientes por Ciudad / Estado")

        # Campo de filtro primario (Ciudad / Fecha inicio / Monto min)
        self.lbl_param1 = ctk.CTkLabel(filter_frame, text="Filtro 1:", font=ctk.CTkFont(size=12))
        self.lbl_param1.grid(row=0, column=2, padx=(10, 2), pady=15, sticky="w")
        self.entry_param1 = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Ciudad, Estado o Nombre",
            width=200,
            height=35
        )
        self.entry_param1.grid(row=0, column=3, padx=5, pady=15, sticky="w")

        # Campo de filtro secundario (Fecha fin)
        self.lbl_param2 = ctk.CTkLabel(filter_frame, text="Filtro 2:", font=ctk.CTkFont(size=12))
        self.lbl_param2.grid(row=0, column=4, padx=(10, 2), pady=15, sticky="w")
        self.entry_param2 = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Fecha Fin (YYYY-MM-DD)",
            width=185,
            height=35
        )
        self.entry_param2.grid(row=0, column=5, padx=5, pady=15, sticky="w")

        # Boton Generar Reporte
        self.btn_generar = ctk.CTkButton(
            filter_frame,
            text="Generar Reporte",
            fg_color="#2980B9",
            hover_color="#2471A3",
            width=145,
            height=35,
            command=self.generate_report
        )
        self.btn_generar.grid(row=0, column=7, padx=10, pady=15, sticky="w")

        # Boton Exportar a PDF
        self.btn_exportar_pdf = ctk.CTkButton(
            filter_frame,
            text="Exportar PDF",
            fg_color="#27AE60",
            hover_color="#1E8449",
            width=130,
            height=35,
            command=self.export_to_pdf
        )
        self.btn_exportar_pdf.grid(row=0, column=8, padx=(5, 15), pady=15, sticky="w")

    def _build_kpis_panel(self):
        """
        Panel de tarjetas KPI dinamico.
        Se reconstruye cada vez que se genera un nuevo reporte.
        """
        self.kpis_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpis_container.grid(row=2, column=0, padx=20, pady=(0, 8), sticky="ew")

    def _render_kpis(self, kpis: dict):
        """Dibuja las tarjetas KPI a partir del diccionario de metricas retornado."""
        # Limpiar cards anteriores
        for widget in self.kpis_container.winfo_children():
            widget.destroy()

        KPI_LABELS = {
            "total_registros":         "Total Registros",
            "total_puntos":            "Puntos Totales",
            "promedio_puntos":         "Promedio Puntos",
            "clientes_con_descuento":  "Clientes c/Descuento",
            "monto_total":             "Monto Total (MXN)",
            "promedio_monto":          "Promedio por Transaccion",
            "con_descuento":           "Ventas c/Descuento",
            "pedidos_surtidos":        "Pedidos Surtidos",
            "pedidos_enviados":        "Pedidos Enviados",
            "factura_maxima":          "Factura Mayor (MXN)",
        }

        col_idx = 0
        for key, val in kpis.items():
            label_text = KPI_LABELS.get(key, key.replace("_", " ").title())

            if isinstance(val, float):
                if "monto" in key or "promedio_monto" in key or "factura" in key:
                    val_text = f"${val:,.2f}"
                else:
                    val_text = f"{val:,.1f}"
            elif isinstance(val, int):
                val_text = f"{val:,}"
            else:
                val_text = str(val)

            card = ctk.CTkFrame(self.kpis_container, corner_radius=8, fg_color="#F2F4F4",
                                border_width=1, border_color="#BDC3C7")
            card.grid(row=0, column=col_idx, padx=6, pady=4, sticky="nsew")
            self.kpis_container.grid_columnconfigure(col_idx, weight=1)

            ctk.CTkLabel(card, text=label_text,
                         font=ctk.CTkFont(size=10), text_color="#7F8C8D").pack(padx=10, pady=(8, 0))
            ctk.CTkLabel(card, text=val_text,
                         font=ctk.CTkFont(size=14, weight="bold"), text_color="#1A252F").pack(padx=10, pady=(2, 8))
            col_idx += 1

    def _build_table_panel(self):
        """Panel inferior con la tabla dinamica de resultados del reporte."""
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.grid_rowconfigure(3, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # Etiqueta de estado / recuento de registros
        self.lbl_status = ctk.CTkLabel(
            self.table_frame,
            text="Listo.",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.lbl_status.pack(anchor="w", padx=12, pady=(8, 2))

        # Los scrollbars deben empaquetarse ANTES del Treeview
        # para que el gestor de geometria los coloque en los bordes correctamente
        scrollbar_y = ttk.Scrollbar(self.table_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        scrollbar_x = ttk.Scrollbar(self.table_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        self.tree_report = ttk.Treeview(
            self.table_frame,
            show="headings",
            height=14,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        self.tree_report.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scrollbar_y.configure(command=self.tree_report.yview)
        scrollbar_x.configure(command=self.tree_report.xview)

    # ------------------------------------------------------------------
    # Logica de reportes
    # ------------------------------------------------------------------

    def on_report_type_change(self, choice):
        """Adapta los placeholders de los filtros segun el reporte seleccionado."""
        if choice == "Clientes por Ciudad / Estado":
            self.lbl_param1.configure(text="Ciudad / Estado:")
            self.entry_param1.configure(
                placeholder_text="Ej: Guadalajara, Jalisco o nombre cliente",
                state="normal"
            )
            self.lbl_param2.configure(text="")
            self.entry_param2.configure(placeholder_text="(no aplica para este reporte)", state="disabled")

        elif choice in ("Ventas por Rango de Fechas", "Compras por Rango de Fechas"):
            self.lbl_param1.configure(text="Fecha Inicio:")
            self.entry_param1.configure(
                placeholder_text="YYYY-MM-DD",
                state="normal"
            )
            self.lbl_param2.configure(text="Fecha Fin:")
            self.entry_param2.configure(placeholder_text="YYYY-MM-DD", state="normal")

        elif choice == "Facturas con Mayores Ventas":
            self.lbl_param1.configure(text="Monto Minimo ($):")
            self.entry_param1.configure(
                placeholder_text="Ej: 500.00  (o vacio para todos)",
                state="normal"
            )
            self.lbl_param2.configure(text="")
            self.entry_param2.configure(placeholder_text="(no aplica para este reporte)", state="disabled")

        # Limpiar tabla al cambiar de tipo
        self._clear_table()
        self._reset_report_state()
        self.lbl_status.configure(text="Seleccione los parametros y presione 'Generar Reporte'.")

    def generate_report(self):
        """Valida la conexion, llama al servicio correspondiente y puebla la tabla."""
        if not check_internet_connection():
            messagebox.showerror(
                "Sin Conexion a Internet",
                "El sistema requiere conexion activa a internet para consultar los reportes.\n"
                "Verifique su red e intente nuevamente."
            )
            return

        tipo = self.combo_tipo_reporte.get()
        param1 = self.entry_param1.get().strip()
        # entry_param2 puede estar deshabilitado; leer de forma segura
        try:
            param2 = self.entry_param2.get().strip()
        except Exception:
            param2 = ""

        self.lbl_status.configure(text="Consultando base de datos...")
        self.update_idletasks()
        self._reset_report_state()

        try:
            if tipo == "Clientes por Ciudad / Estado":
                rows_data, kpis = GestorReportes.generarReporteClientesPorUbicacion(filtro=param1 or None)
                headers = ["ID", "Nombre Cliente", "RFC", "Ciudad", "Estado", "Puntos", "Correo", "Telefono"]
                col_keys = ["id_cliente", "nombre", "rfc", "ciudad", "estado", "puntos", "correo", "telefono"]
                col_widths = [55, 185, 130, 130, 125, 65, 170, 110]

            elif tipo == "Ventas por Rango de Fechas":
                rows_data, kpis = GestorReportes.generarReporteVentasPorFecha(inicio=param1 or None, fin=param2 or None)
                headers = ["ID Venta", "Fecha / Hora", "Cliente", "Cajero", "Metodo Pago", "Descuento", "Total ($)"]
                col_keys = ["id_venta", "fecha_hora", "cliente", "cajero", "metodo_pago", "descuento", "total_venta"]
                col_widths = [75, 150, 175, 145, 110, 75, 95]

            elif tipo == "Compras por Rango de Fechas":
                rows_data, kpis = GestorReportes.generarReporteComprasPorFecha(inicio=param1 or None, fin=param2 or None)
                headers = ["ID Compra", "Fecha / Hora", "Proveedor", "Usuario", "Estado Pedido", "Total ($)"]
                col_keys = ["id_compra", "fecha_hora", "proveedor", "usuario", "estado_pedido", "total_compra"]
                col_widths = [80, 155, 185, 145, 110, 100]

            elif tipo == "Facturas con Mayores Ventas":
                try:
                    monto_min = float(param1) if param1 else 0.0
                except ValueError:
                    messagebox.showerror("Parametro Invalido", "El monto minimo debe ser un numero valido (Ej: 500.00).")
                    self.lbl_status.configure(text="Error: parametro invalido.")
                    return
                rows_data, kpis = GestorReportes.generarReporteFacturasMayorVenta(limite=50, monto_minimo=monto_min)
                headers = ["ID Factura", "ID Venta", "Fecha Emision", "RFC Receptor", "Cliente", "Monto Venta ($)"]
                col_keys = ["id_factura", "id_venta", "fecha_emision", "rfc_receptor", "cliente", "monto_venta"]
                col_widths = [80, 75, 150, 130, 170, 115]
            else:
                return

            # Guardar estado actual para exportar
            self._current_rows = rows_data
            self._current_kpis = kpis
            self._current_headers = headers
            self._current_col_keys = col_keys

            # Actualizar KPIs
            self._render_kpis(kpis)

            # Poblar tabla
            self._clear_table()
            self._configure_columns(headers, col_widths)

            for rec in rows_data:
                values_row = []
                for ck in col_keys:
                    val = rec.get(ck, "")
                    if isinstance(val, float):
                        val = f"${val:,.2f}"
                    values_row.append(val)
                self.tree_report.insert("", "end", values=values_row)

            count = kpis.get("total_registros", len(rows_data))
            self.lbl_status.configure(text=f"Reporte generado: {count} registro(s) encontrado(s).")

        except ValueError as e:
            messagebox.showerror("Parametro Invalido", str(e))
            self.lbl_status.configure(text="Error: parametro invalido.")
        except Exception as e:
            messagebox.showerror("Error al Generar Reporte", f"Ocurrio un error al consultar los datos:\n{e}")
            self.lbl_status.configure(text="Error al generar el reporte.")
            self._reset_report_state()

    def export_to_pdf(self):
        """Exporta el reporte activo a un archivo PDF con membrete institucional."""
        if not self._current_rows and not self._current_kpis:
            messagebox.showwarning(
                "Sin Reporte Activo",
                "Primero genere un reporte antes de exportar.\n"
                "Seleccione el tipo, configure los filtros y presione 'Generar Reporte'."
            )
            return

        if not check_internet_connection():
            messagebox.showerror(
                "Sin Conexion a Internet",
                "Se requiere conexion activa para exportar el reporte."
            )
            return

        tipo = self.combo_tipo_reporte.get()
        param1_val = self.entry_param1.get().strip()
        # entry_param2 puede estar deshabilitado; leer de forma segura
        try:
            param2_val = self.entry_param2.get().strip()
        except Exception:
            param2_val = ""

        # Descripcion de filtros para el encabezado del PDF
        partes = []
        if param1_val:
            partes.append(f"Filtro 1: {param1_val}")
        if param2_val:
            partes.append(f"Filtro 2: {param2_val}")
        filter_desc = " | ".join(partes) if partes else "Sin filtros aplicados"

        # Construir filas para el PDF usando col_keys
        col_keys = getattr(self, "_current_col_keys", [])
        pdf_rows = []
        for rec in self._current_rows:
            row_vals = []
            for ck in col_keys:
                val = rec.get(ck, "")
                if isinstance(val, float):
                    val = f"${val:,.2f}"
                row_vals.append(str(val) if val is not None else "")
            pdf_rows.append(row_vals)

        ok, msg, path = export_report_to_pdf(
            report_title=tipo,
            filter_description=filter_desc,
            headers=self._current_headers,
            rows_data=pdf_rows,
            kpis=self._current_kpis
        )

        if ok:
            messagebox.showinfo(
                "PDF Generado Correctamente",
                f"El reporte fue exportado exitosamente.\n\nRuta del archivo:\n{path}"
            )
        else:
            messagebox.showerror("Error al Exportar PDF", f"No se pudo generar el archivo PDF:\n{msg}")

    # ------------------------------------------------------------------
    # Utilidades de tabla
    # ------------------------------------------------------------------

    def _clear_table(self):
        """Limpia todos los registros visibles de la tabla."""
        self.tree_report.delete(*self.tree_report.get_children())

    def _reset_report_state(self):
        self._current_rows = []
        self._current_kpis = {}
        self._current_headers = []
        self._current_col_keys = []
        self._render_kpis({})

    def _configure_columns(self, headers: list, widths: list):
        """Reconfigura columnas y encabezados de la tabla Treeview."""
        self.tree_report.configure(columns=headers)
        for col, w in zip(headers, widths):
            self.tree_report.heading(col, text=col)
            self.tree_report.column(col, width=w, anchor="w", minwidth=50)


# ----------------------------------------------------------------------
# Bloque de prueba unitaria independiente
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import tkinter as tk

    print("Iniciando prueba unitaria de ReportsView (modo standalone)...")

    root = ctk.CTk()
    root.title("Prueba - Modulo de Reportes")
    root.geometry("1280x780")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Simular rol de Gerente
    view = ReportsView(parent=root, role="Gerente")
    view.grid(row=0, column=0, sticky="nsew")

    print("Vista de Reportes cargada correctamente.")
    root.mainloop()
