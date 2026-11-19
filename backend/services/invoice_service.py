import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.database.connection import get_connection

def generate_invoice_pdf(id_venta: int) -> tuple[bool, str, str]:
    """
    Genera el archivo PDF formal de la factura de una venta registrada:
    1. Consulta la informacion de la venta, cliente y detalles en PostgreSQL.
    2. Construye el documento PDF con membrete, logo de la farmacia y desglose.
    3. Registra la ruta en la tabla Facturas de la base de datos.
    
    Retorna: (exito: bool, mensaje: str, ruta_pdf: str)
    """
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # 1. Consultar encabezado de la venta y datos del cliente
            query_venta = """
                SELECT 
                    v.id_venta, 
                    v.fecha_hora, 
                    v.metodo_pago, 
                    v.descuento_aplicado, 
                    v.total_venta,
                    c.id_cliente,
                    c.nombre AS cliente_nombre,
                    c.rfc AS cliente_rfc,
                    c.correo AS cliente_correo,
                    COALESCE(c.ciudad, 'Guadalajara') AS cliente_ciudad,
                    COALESCE(c.estado, 'Jalisco') AS cliente_estado,
                    u.nombre AS cajero_nombre
                FROM Ventas v
                JOIN Clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN Usuarios u ON v.id_usuario = u.id_usuario
                WHERE v.id_venta = %s;
            """
            cursor.execute(query_venta, (id_venta,))
            venta_row = cursor.fetchone()
            if not venta_row:
                return False, f"No se encontro ninguna venta con el ID #{id_venta}.", ""

            (
                v_id, v_fecha, v_metodo, v_descuento_aplicado, v_total,
                c_id, c_nombre, c_rfc, c_correo, c_ciudad, c_estado, u_nombre
            ) = venta_row

            # 2. Consultar desglose de productos vendidos
            query_detalles = """
                SELECT 
                    p.folio, 
                    p.nombre, 
                    dv.cantidad, 
                    dv.precio_unitario, 
                    dv.subtotal
                FROM Detalle_Ventas dv
                JOIN Productos p ON dv.id_producto = p.id_producto
                WHERE dv.id_venta = %s
                ORDER BY dv.id_detalle_venta ASC;
            """
            cursor.execute(query_detalles, (id_venta,))
            detalles = cursor.fetchall()

            # 3. Preparar directorio de facturas
            output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../facturas"))
            os.makedirs(output_dir, exist_ok=True)
            pdf_filename = f"factura_venta_{v_id}_{c_rfc}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)

            # 4. Construccion del documento PDF con ReportLab
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            story = []
            styles = getSampleStyleSheet()

            style_title = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor("#2C3E50"),
                leading=22
            )
            style_sub = ParagraphStyle(
                'DocSub',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor("#555555"),
                leading=12
            )
            style_bold = ParagraphStyle(
                'DocBold',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor("#1A252F"),
                fontName="Helvetica-Bold",
                leading=12
            )

            # Logotipo de la Farmacia
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/assets/logo.png"))
            if os.path.exists(logo_path):
                try:
                    logo_img = Image(logo_path, width=1.5*inch, height=0.75*inch)
                except Exception:
                    logo_img = Paragraph("<b>FARMACIA CUCEI</b>", style_title)
            else:
                logo_img = Paragraph("<b>FARMACIA CUCEI</b>", style_title)

            # Encabezado (Logo a la izquierda | Datos Fiscales a la derecha)
            header_data = [
                [
                    logo_img,
                    Paragraph(
                        "<b>FARMACIA CUCEI S.A. DE C.V.</b><br/>"
                        "RFC: FCU240101XYZ<br/>"
                        "Av. Revolucion 1500, Col. Olimpica<br/>"
                        "Guadalajara, Jalisco, C.P. 44430<br/>"
                        "Regimen Fiscal: 601 General de Ley Personas Morales",
                        style_sub
                    ),
                    Paragraph(
                        f"<b>FACTURA ELECTRONICA</b><br/>"
                        f"<b>Folio:</b> FAC-{v_id:05d}<br/>"
                        f"<b>Fecha:</b> {str(v_fecha)[:16]}<br/>"
                        f"<b>Metodo Pago:</b> {v_metodo}<br/>"
                        f"<b>Cajero:</b> {u_nombre or 'General'}",
                        style_sub
                    )
                ]
            ]
            header_table = Table(header_data, colWidths=[1.8*inch, 3.2*inch, 2.2*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor("#2C3E50")),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 14))

            # Datos del Cliente Receptor
            client_data = [
                [
                    Paragraph("<b>DATOS DEL RECEPTOR (CLIENTE)</b>", style_bold),
                    Paragraph(f"<b>RFC:</b> {c_rfc}", style_sub)
                ],
                [
                    Paragraph(f"<b>Nombre:</b> {c_nombre}", style_sub),
                    Paragraph(f"<b>Correo:</b> {c_correo or 'N/A'}", style_sub)
                ],
                [
                    Paragraph(f"<b>Ubicacion:</b> {c_ciudad}, {c_estado}", style_sub),
                    Paragraph(f"<b>Uso CFDI:</b> G03 - Gastos en general", style_sub)
                ]
            ]
            client_table = Table(client_data, colWidths=[4.2*inch, 3.0*inch])
            client_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F9F9")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ECF0F1")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(client_table)
            story.append(Spacer(1, 14))

            # Tabla de Productos y Conceptos
            prod_headers = ["Folio", "Descripcion del Producto", "Cant.", "P. Unitario", "Subtotal"]
            table_rows = [prod_headers]

            subtotal_bruto = 0.0
            for det in detalles:
                folio, nombre, cant, p_unit, subt = det
                subtotal_bruto += float(subt)
                table_rows.append([
                    folio or "S/F",
                    nombre,
                    str(cant),
                    f"${float(p_unit):,.2f}",
                    f"${float(subt):,.2f}"
                ])

            prod_table = Table(table_rows, colWidths=[1.1*inch, 3.3*inch, 0.8*inch, 1.0*inch, 1.0*inch])
            prod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9EBEA") if False else colors.HexColor("#F8F9FA")]),
            ]))
            story.append(prod_table)
            story.append(Spacer(1, 12))

            # Resumen de Totales y Descuento
            descuento_monto = round(subtotal_bruto * 0.10, 2) if v_descuento_aplicado else 0.0
            total_neto = float(v_total)

            totales_data = [
                ["Subtotal:", f"${subtotal_bruto:,.2f} MXN"],
                ["Descuento Lealtad (10%):", f"-${descuento_monto:,.2f} MXN" if v_descuento_aplicado else "$0.00 MXN"],
                ["TOTAL A PAGAR:", f"${total_neto:,.2f} MXN"]
            ]
            totales_table = Table(totales_data, colWidths=[5.2*inch, 2.0*inch])
            totales_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#27AE60")),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor("#2C3E50")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(totales_table)
            story.append(Spacer(1, 25))

            # Pie de Pagina Legal
            legal_text = (
                "Este documento es una representacion impresa de un Comprobante Fiscal Digital por Internet (CFDI). "
                "Efectos fiscales al pago. Emitido a traves del sistema de gestion comercial Farmacia CUCEI."
            )
            story.append(Paragraph(legal_text, ParagraphStyle('Legal', parent=styles['Italic'], fontSize=8, textColor=colors.gray, alignment=1)))

            # 5. Generar PDF
            doc.build(story)

            # 6. Registrar en tabla Facturas
            query_insert_factura = """
                INSERT INTO Facturas (id_venta, rfc_receptor, ruta_archivo_pdf)
                VALUES (%s, %s, %s)
                RETURNING id_factura;
            """
            cursor.execute(query_insert_factura, (v_id, c_rfc, pdf_path))
            id_factura = cursor.fetchone()[0]
            connection.commit()

            return True, f"Factura #{id_factura} generada exitosamente en PDF.", pdf_path

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[Error al generar factura PDF]: {e}")
        return False, f"Fallo al generar factura: {e}", ""
    finally:
        if connection:
            connection.close()

def get_all_invoices() -> list:
    """Retorna la lista de todas las facturas generadas."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    f.id_factura, 
                    f.id_venta, 
                    f.fecha_emision, 
                    f.rfc_receptor, 
                    f.ruta_archivo_pdf,
                    v.total_venta,
                    c.nombre AS cliente_nombre
                FROM Facturas f
                JOIN Ventas v ON f.id_venta = v.id_venta
                LEFT JOIN Clientes c ON v.id_cliente = c.id_cliente
                ORDER BY f.fecha_emision DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            invoices = []
            for r in rows:
                invoices.append({
                    "id_factura": r[0],
                    "id_venta": r[1],
                    "fecha_emision": str(r[2]),
                    "rfc_receptor": r[3],
                    "ruta_archivo_pdf": r[4],
                    "total_venta": float(r[5]),
                    "cliente_nombre": r[6] or "Publico General"
                })
            return invoices
    except Exception as e:
        print(f"[Error al consultar facturas]: {e}")
        return []
    finally:
        if connection:
            connection.close()
