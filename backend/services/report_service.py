"""
Servicio de Reportes Gerenciales y Facturacion para Farmacia CUCEI.
Maneja las consultas analiticas a PostgreSQL (Supabase) y la generacion
formal de reportes ejecutivos en formato PDF utilizando ReportLab.
"""

import os
import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.database.connection import get_connection

def parse_date_boundary(date_str: Optional[str], is_end: bool = False) -> Optional[str]:
    """
    Normaliza y valida un string de fecha en formato YYYY-MM-DD.
    Para fecha inicial anade '00:00:00'.
    Para fecha final anade '23:59:59' para incluir todo el dia.
    Retorna None si la cadena esta vacia o es invalida.
    """
    if not date_str or not str(date_str).strip():
        return None
    
    clean_str = str(date_str).strip()
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", clean_str)
    if not match:
        # Intento de formato alternativo DD/MM/YYYY
        match_alt = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", clean_str)
        if match_alt:
            day, month, year = match_alt.groups()
            clean_str = f"{year}-{int(month):02d}-{int(day):02d}"
        else:
            return None

    try:
        dt = datetime.strptime(clean_str, "%Y-%m-%d")
        if is_end:
            return dt.strftime("%Y-%m-%d 23:59:59")
        return dt.strftime("%Y-%m-%d 00:00:00")
    except ValueError:
        return None

def get_clients_by_location(
    filtro: Optional[str] = None, 
    ciudad: Optional[str] = None, 
    estado: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Consulta clientes agrupados o filtrados por ubicacion geografica (ciudad / estado).
    Calcula metricas de fidelidad y conteos agregados.
    
    Retorna: (lista_de_clientes, resumen_kpis)
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    c.id_cliente,
                    c.nombre,
                    COALESCE(c.rfc, 'S/RFC') AS rfc,
                    COALESCE(c.ciudad, 'No especificada') AS ciudad,
                    COALESCE(c.estado, 'No especificado') AS estado,
                    COALESCE(c.puntos_acumulados, 0) AS puntos_acumulados,
                    COALESCE(c.correo, '') AS correo,
                    COALESCE(c.telefono, '') AS telefono
                FROM Clientes c
                WHERE 1=1
            """
            params: List[Any] = []

            if filtro and filtro.strip():
                f_val = f"%{filtro.strip()}%"
                query += " AND (c.ciudad ILIKE %s OR c.estado ILIKE %s OR c.nombre ILIKE %s)"
                params.extend([f_val, f_val, f_val])
            else:
                if ciudad and ciudad.strip():
                    query += " AND c.ciudad ILIKE %s"
                    params.append(f"%{ciudad.strip()}%")
                if estado and estado.strip():
                    query += " AND c.estado ILIKE %s"
                    params.append(f"%{estado.strip()}%")

            query += " ORDER BY c.estado ASC, c.ciudad ASC, c.nombre ASC;"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            clients = []
            total_puntos = 0
            con_descuento = 0

            for r in rows:
                puntos = int(r[5]) if r[5] is not None else 0
                total_puntos += puntos
                if puntos >= 50:
                    con_descuento += 1

                clients.append({
                    "id_cliente": r[0],
                    "nombre": r[1],
                    "rfc": r[2],
                    "ciudad": r[3],
                    "estado": r[4],
                    "puntos": puntos,
                    "correo": r[6],
                    "telefono": r[7]
                })

            total_reg = len(clients)
            promedio_puntos = round(total_puntos / total_reg, 1) if total_reg > 0 else 0.0

            kpis = {
                "total_registros": total_reg,
                "total_puntos": total_puntos,
                "promedio_puntos": promedio_puntos,
                "clientes_con_descuento": con_descuento
            }

            return clients, kpis
    except Exception as e:
        print(f"[Error al consultar reporte de clientes por ubicacion]: {e}")
        return [], {"total_registros": 0, "total_puntos": 0, "promedio_puntos": 0.0, "clientes_con_descuento": 0}
    finally:
        if connection:
            connection.close()

def get_sales_by_date_range(
    fecha_inicio: Optional[str] = None, 
    fecha_fin: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Consulta transacciones de venta dentro de un intervalo de fechas.
    Incluye datos del cliente, usuario/cajero y desglose financiero.
    
    Retorna: (lista_de_ventas, resumen_kpis)
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    v.id_venta,
                    v.fecha_hora,
                    COALESCE(c.nombre, 'Publico General') AS cliente_nombre,
                    COALESCE(u.nombre, 'Sin Cajero') AS cajero_nombre,
                    COALESCE(v.metodo_pago, 'Efectivo') AS metodo_pago,
                    COALESCE(v.descuento_aplicado, FALSE) AS descuento_aplicado,
                    COALESCE(v.total_venta, 0.00) AS total_venta
                FROM Ventas v
                LEFT JOIN Clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN Usuarios u ON v.id_usuario = u.id_usuario
                WHERE 1=1
            """
            params: List[Any] = []

            f_ini = parse_date_boundary(fecha_inicio, is_end=False)
            if f_ini:
                query += " AND v.fecha_hora >= %s"
                params.append(f_ini)

            f_fin = parse_date_boundary(fecha_fin, is_end=True)
            if f_fin:
                query += " AND v.fecha_hora <= %s"
                params.append(f_fin)

            query += " ORDER BY v.fecha_hora DESC;"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            sales = []
            monto_total = 0.0
            ventas_descuento = 0

            for r in rows:
                total_v = float(r[6]) if r[6] is not None else 0.0
                monto_total += total_v
                desc_ap = bool(r[5])
                if desc_ap:
                    ventas_descuento += 1

                fecha_fmt = str(r[1])[:19] if r[1] else "N/A"

                sales.append({
                    "id_venta": r[0],
                    "fecha_hora": fecha_fmt,
                    "cliente": r[2],
                    "cajero": r[3],
                    "metodo_pago": r[4],
                    "descuento": "Si" if desc_ap else "No",
                    "total_venta": total_v
                })

            total_reg = len(sales)
            promedio_monto = round(monto_total / total_reg, 2) if total_reg > 0 else 0.0

            kpis = {
                "total_registros": total_reg,
                "monto_total": round(monto_total, 2),
                "promedio_monto": promedio_monto,
                "con_descuento": ventas_descuento
            }

            return sales, kpis
    except Exception as e:
        print(f"[Error al consultar reporte de ventas por fecha]: {e}")
        return [], {"total_registros": 0, "monto_total": 0.0, "promedio_monto": 0.0, "con_descuento": 0}
    finally:
        if connection:
            connection.close()

def get_purchases_by_date_range(
    fecha_inicio: Optional[str] = None, 
    fecha_fin: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Consulta compras realizadas a proveedores dentro de un rango de fechas.
    Agrega estados de pedido (Enviado / Surtido) y totales monetarios.
    
    Retorna: (lista_de_compras, resumen_kpis)
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    c.id_compra,
                    c.fecha_hora,
                    COALESCE(p.razon_social, 'Sin Proveedor') AS proveedor_nombre,
                    COALESCE(u.nombre, 'Sin Asignar') AS usuario_nombre,
                    COALESCE(c.estado_pedido, 'Pendiente') AS estado_pedido,
                    COALESCE(c.total_compra, 0.00) AS total_compra
                FROM Compras c
                LEFT JOIN Proveedores p ON c.id_proveedor = p.id_proveedor
                LEFT JOIN Usuarios u ON c.id_usuario = u.id_usuario
                WHERE 1=1
            """
            params: List[Any] = []

            f_ini = parse_date_boundary(fecha_inicio, is_end=False)
            if f_ini:
                query += " AND c.fecha_hora >= %s"
                params.append(f_ini)

            f_fin = parse_date_boundary(fecha_fin, is_end=True)
            if f_fin:
                query += " AND c.fecha_hora <= %s"
                params.append(f_fin)

            query += " ORDER BY c.fecha_hora DESC;"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            purchases = []
            monto_total = 0.0
            pedidos_surtidos = 0
            pedidos_enviados = 0

            for r in rows:
                total_c = float(r[5]) if r[5] is not None else 0.0
                monto_total += total_c
                estado = r[4]
                if estado == "Surtido":
                    pedidos_surtidos += 1
                elif estado == "Enviado":
                    pedidos_enviados += 1

                fecha_fmt = str(r[1])[:19] if r[1] else "N/A"

                purchases.append({
                    "id_compra": r[0],
                    "fecha_hora": fecha_fmt,
                    "proveedor": r[2],
                    "usuario": r[3],
                    "estado_pedido": estado,
                    "total_compra": total_c
                })

            total_reg = len(purchases)
            promedio_monto = round(monto_total / total_reg, 2) if total_reg > 0 else 0.0

            kpis = {
                "total_registros": total_reg,
                "monto_total": round(monto_total, 2),
                "promedio_monto": promedio_monto,
                "pedidos_surtidos": pedidos_surtidos,
                "pedidos_enviados": pedidos_enviados
            }

            return purchases, kpis
    except Exception as e:
        print(f"[Error al consultar reporte de compras por fecha]: {e}")
        return [], {"total_registros": 0, "monto_total": 0.0, "promedio_monto": 0.0, "pedidos_surtidos": 0, "pedidos_enviados": 0}
    finally:
        if connection:
            connection.close()

def get_invoices_by_highest_sales(
    limite: int = 20, 
    monto_minimo: float = 0.0
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Consulta facturas emitidas correspondientes a las ventas con mayores importes monetarios.
    Aplica filtros opcionales de monto minimo y cantidad de registros.
    
    Retorna: (lista_de_facturas, resumen_kpis)
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    f.id_factura,
                    f.id_venta,
                    f.fecha_emision,
                    COALESCE(f.rfc_receptor, 'XAXX010101000') AS rfc_receptor,
                    COALESCE(c.nombre, 'Publico General') AS cliente_nombre,
                    COALESCE(v.total_venta, 0.00) AS total_venta,
                    COALESCE(f.ruta_archivo_pdf, '') AS ruta_archivo_pdf
                FROM Facturas f
                JOIN Ventas v ON f.id_venta = v.id_venta
                LEFT JOIN Clientes c ON v.id_cliente = c.id_cliente
                WHERE 1=1
            """
            params: List[Any] = []

            if monto_minimo and float(monto_minimo) > 0:
                query += " AND v.total_venta >= %s"
                params.append(float(monto_minimo))

            query += " ORDER BY v.total_venta DESC, f.fecha_emision DESC"

            # Limite de seguridad
            lim_val = max(1, min(int(limite), 100))
            query += f" LIMIT {lim_val};"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            invoices = []
            monto_total = 0.0
            factura_max = 0.0

            for r in rows:
                total_v = float(r[5]) if r[5] is not None else 0.0
                monto_total += total_v
                if total_v > factura_max:
                    factura_max = total_v

                fecha_fmt = str(r[2])[:19] if r[2] else "N/A"

                invoices.append({
                    "id_factura": r[0],
                    "id_venta": r[1],
                    "fecha_emision": fecha_fmt,
                    "rfc_receptor": r[3],
                    "cliente": r[4],
                    "monto_venta": total_v,
                    "ruta_archivo_pdf": r[6]
                })

            total_reg = len(invoices)
            promedio_monto = round(monto_total / total_reg, 2) if total_reg > 0 else 0.0

            kpis = {
                "total_registros": total_reg,
                "monto_total": round(monto_total, 2),
                "promedio_monto": promedio_monto,
                "factura_maxima": round(factura_max, 2)
            }

            return invoices, kpis
    except Exception as e:
        print(f"[Error al consultar reporte de facturas con mayores ventas]: {e}")
        return [], {"total_registros": 0, "monto_total": 0.0, "promedio_monto": 0.0, "factura_maxima": 0.0}
    finally:
        if connection:
            connection.close()

def export_report_to_pdf(
    report_title: str,
    filter_description: str,
    headers: List[str],
    rows_data: List[List[Any]],
    kpis: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, str]:
    """
    Construye y almacena un documento PDF formal con ReportLab en orientacion apaisada (Landscape)
    conteniendo el membrete institucional, resumen ejecutivo de KPIs y tabla de detalle.
    
    Retorna: (exito: bool, mensaje: str, ruta_archivo_pdf: str)
    """
    try:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../reportes"))
        os.makedirs(output_dir, exist_ok=True)

        clean_slug = re.sub(r'[^a-zA-Z0-9_]', '_', report_title.lower())
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_{clean_slug}_{timestamp_str}.pdf"
        pdf_path = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(letter),
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#2C3E50"),
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#555555")
        )
        kpi_header_style = ParagraphStyle(
            'KpiHeader',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#7F8C8D"),
            alignment=1
        )
        kpi_value_style = ParagraphStyle(
            'KpiValue',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1A252F"),
            fontName="Helvetica-Bold",
            alignment=1
        )
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2C3E50")
        )
        cell_style_bold = ParagraphStyle(
            'TableCellBold',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName="Helvetica-Bold"
        )

        # 1. Membrete Institucional con Logo
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/assets/logo.png"))
        if os.path.exists(logo_path):
            try:
                logo_elem = Image(logo_path, width=1.4*inch, height=0.7*inch)
            except Exception:
                logo_elem = Paragraph("<b>FARMACIA CUCEI</b>", title_style)
        else:
            logo_elem = Paragraph("<b>FARMACIA CUCEI</b>", title_style)

        now_formatted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header_data = [
            [
                logo_elem,
                Paragraph(
                    "<b>FARMACIA CUCEI S.A. DE C.V.</b><br/>"
                    "RFC: FCU240101XYZ<br/>"
                    "Av. Revolucion 1500, Guadalajara, Jalisco<br/>"
                    "Sistema de Control y Administracion Farmaceutica",
                    subtitle_style
                ),
                Paragraph(
                    f"<b>{report_title.upper()}</b><br/>"
                    f"<b>Filtros:</b> {filter_description}<br/>"
                    f"<b>Emision:</b> {now_formatted}<br/>"
                    "<b>Clasificacion:</b> Reporte Gerencial Confidencial",
                    subtitle_style
                )
            ]
        ]

        header_table = Table(header_data, colWidths=[1.8*inch, 4.0*inch, 4.2*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor("#2C3E50")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # 2. Resumen Ejecutivo (KPIs Cards)
        if kpis:
            kpi_cols = []
            for k, v in kpis.items():
                label_fmt = k.replace("_", " ").title()
                if "monto" in k or "total_venta" in k or "total_compra" in k or "factura" in k:
                    val_str = f"${float(v):,.2f} MXN"
                elif isinstance(v, float):
                    val_str = f"{v:,.1f}"
                elif isinstance(v, int):
                    val_str = f"{v:,}"
                else:
                    val_str = str(v)

                cell_content = [
                    Paragraph(label_fmt, kpi_header_style),
                    Spacer(1, 2),
                    Paragraph(val_str, kpi_value_style)
                ]
                kpi_cols.append(cell_content)

            if kpi_cols:
                col_width = (10.0 * inch) / len(kpi_cols)
                kpi_table = Table([kpi_cols], colWidths=[col_width] * len(kpi_cols))
                kpi_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F2F4F4")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                story.append(kpi_table)
                story.append(Spacer(1, 12))

        # 3. Tabla Detallada de Datos
        table_rows = []
        # Fila de Encabezados
        header_row = [Paragraph(str(h), cell_style_bold) for h in headers]
        table_rows.append(header_row)

        if not rows_data:
            empty_msg = [Paragraph("No se encontraron registros bajo los parametros seleccionados.", cell_style)]
            empty_row = empty_msg + [Paragraph("", cell_style)] * (len(headers) - 1)
            table_rows.append(empty_row)
        else:
            for row in rows_data:
                formatted_cells = []
                for item in row:
                    item_str = str(item) if item is not None else ""
                    formatted_cells.append(Paragraph(item_str, cell_style))
                table_rows.append(formatted_cells)

        num_cols = len(headers)
        available_width = 10.0 * inch
        col_width = available_width / num_cols
        data_table = Table(table_rows, colWidths=[col_width] * num_cols, repeatRows=1)

        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ]

        # Coloreado alternado de filas
        for i in range(1, len(table_rows)):
            bg = colors.HexColor("#FFFFFF") if i % 2 != 0 else colors.HexColor("#F8F9F9")
            t_style.append(('BACKGROUND', (0, i), (-1, i), bg))

        data_table.setStyle(TableStyle(t_style))
        story.append(data_table)

        # 4. Pie de pagina institucional
        story.append(Spacer(1, 15))
        footer_text = Paragraph(
            "Este documento es un informe administrativo y financiero interno generado por el Sistema Farmacia CUCEI. "
            "Contiene informacion protegida y clasificada para la toma de decisiones gerenciales.",
            subtitle_style
        )
        story.append(footer_text)

        # Compilar documento
        doc.build(story)
        return True, "Reporte exportado exitosamente a formato PDF.", pdf_path

    except Exception as e:
        print(f"[Error al exportar reporte a PDF]: {e}")
        return False, f"Error al generar archivo PDF del reporte: {str(e)}", ""

if __name__ == "__main__":
    # Prueba unitaria local de generacion de reporte
    print("Iniciando prueba unitaria de report_service...")
    test_headers = ["ID", "Nombre", "Ciudad", "Estado", "Puntos"]
    test_rows = [
        ["1", "Juan Perez", "Guadalajara", "Jalisco", "30"],
        ["2", "Maria Lopez", "Zapopan", "Jalisco", "55"],
        ["3", "Carlos Sanchez", "Monterrey", "Nuevo Leon", "10"],
    ]
    test_kpis = {
        "total_registros": 3,
        "total_puntos": 95,
        "promedio_puntos": 31.7,
        "clientes_con_descuento": 1
    }
    ok, msg, path = export_report_to_pdf(
        "Reporte de Clientes de Prueba",
        "Prueba de sistema sin filtros",
        test_headers,
        test_rows,
        test_kpis
    )
    print(f"Resultado PDF: {ok} | {msg} | Ruta: {path}")
