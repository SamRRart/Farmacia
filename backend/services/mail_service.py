import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from backend.services.connectivity_service import check_internet_connection

def get_smtp_config() -> dict:
    return {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "sender": os.getenv("SMTP_SENDER", "Farmacia CUCEI <notificaciones@farmaciacucei.com>")
    }

def send_invoice_email(
    to_email: str,
    client_name: str,
    rfc: str,
    pdf_path: str,
    total_amount: float
) -> tuple[bool, str]:
    """
    Envia por correo electronico la factura en formato PDF al cliente.
    Verifica primero la existencia de conexion a internet activa.
    """
    if not check_internet_connection():
        return False, "Operacion bloqueada: No se detecto conexion activa a internet para enviar el correo."

    to_email = (to_email or "").strip()
    if not to_email or "@" not in to_email:
        return False, "La direccion de correo del cliente no es valida."

    if not os.path.exists(pdf_path):
        return False, f"El archivo PDF de factura no fue encontrado en: {pdf_path}"

    try:
        cfg = get_smtp_config()
        msg = MIMEMultipart()
        msg["From"] = cfg["sender"]
        msg["To"] = to_email
        msg["Subject"] = f"Factura Electronica - Farmacia CUCEI (RFC: {rfc})"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="background-color: #2C3E50; color: white; padding: 15px; text-align: center;">
                <h2>Farmacia CUCEI</h2>
                <p>Comprobante Fiscal Digital</p>
            </div>
            <div style="padding: 20px;">
                <p>Estimado/a <strong>{client_name}</strong>,</p>
                <p>Agradecemos su compra en Farmacia CUCEI. Adjunto a este correo encontrara su factura digital correspondiente.</p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>RFC Receptor:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{rfc}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Total de Venta:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd; color: #27AE60; font-weight: bold;">${total_amount:,.2f} MXN</td>
                    </tr>
                </table>
                <p style="margin-top: 20px; font-size: 12px; color: gray;">
                    Farmacia CUCEI - Av. Revolucion 1500, Guadalajara, Jalisco.<br>
                    Este es un correo automatico, por favor no responda a este mensaje.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body_html, "html"))

        # Adjuntar archivo PDF
        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_filename = os.path.basename(pdf_path)
            pdf_attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
            msg.attach(pdf_attachment)

        # Si no estan configuradas las credenciales SMTP en .env, registrar el intento
        if not cfg["user"] or not cfg["password"]:
            message = (
                f"No se envio la factura a {to_email}: faltan las credenciales SMTP."
            )
            print(f"[Aviso SMTP]: {message}")
            return False, message

        # Envio real por SMTP
        with smtplib.SMTP(cfg["server"], cfg["port"], timeout=10) as server:
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)

        return True, f"Factura enviada exitosamente al correo {to_email}."

    except Exception as e:
        print(f"[Error SMTP al enviar factura]: {e}")
        return False, f"Error al enviar correo por SMTP: {e}"

def send_restock_order_email(
    provider_email: str,
    provider_name: str,
    order_id: int,
    items_list: list,
    total_amount: float
) -> tuple[bool, str]:
    """
    Envia una orden de compra o reabastecimiento (Restock) por correo al proveedor.
    """
    if not check_internet_connection():
        return False, "Operacion bloqueada: No se detecto conexion activa a internet para notificar al proveedor."

    provider_email = (provider_email or "").strip()
    if not provider_email or "@" not in provider_email:
        return False, "El proveedor no cuenta con una direccion de correo valida."

    try:
        cfg = get_smtp_config()
        msg = MIMEMultipart()
        msg["From"] = cfg["sender"]
        msg["To"] = provider_email
        msg["Subject"] = f"Orden de Reabastecimiento #{order_id} - Farmacia CUCEI"

        items_rows = "".join(
            f"<tr><td style='padding:6px;border:1px solid #ddd;'>{it.get('nombre', 'Producto')}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;text-align:center;'>{it.get('cantidad', 1)}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;text-align:right;'>${it.get('precio_compra_unitario', 0.0):.2f}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;text-align:right;'>${it.get('subtotal', 0.0):.2f}</td></tr>"
            for it in items_list
        )

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="background-color: #2980B9; color: white; padding: 12px; text-align: center;">
                <h3>Solicitud de Reabastecimiento - Farmacia CUCEI</h3>
            </div>
            <div style="padding: 15px;">
                <p>Estimados representantes de <strong>{provider_name}</strong>,</p>
                <p>Por medio del presente solicitamos el surtido de la siguiente orden de compra (ID #{order_id}):</p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="padding:6px;border:1px solid #ddd;">Producto</th>
                            <th style="padding:6px;border:1px solid #ddd;">Cantidad</th>
                            <th style="padding:6px;border:1px solid #ddd;">P. Compra</th>
                            <th style="padding:6px;border:1px solid #ddd;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_rows}
                    </tbody>
                </table>
                <p style="text-align: right; font-size: 14px; font-weight: bold; margin-top: 10px;">
                    Total Estimado de la Orden: ${total_amount:,.2f} MXN
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body_html, "html"))

        if not cfg["user"] or not cfg["password"]:
            message = (
                f"No se envio la orden #{order_id}: faltan las credenciales SMTP para "
                f"notificar a {provider_name} ({provider_email})."
            )
            print(f"[Aviso SMTP]: {message}")
            return False, message

        with smtplib.SMTP(cfg["server"], cfg["port"], timeout=10) as server:
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)

        return True, f"Orden de compra notificada exitosamente a {provider_email}."

    except Exception as e:
        print(f"[Error SMTP en restock]: {e}")
        return False, f"Fallo al enviar correo al proveedor: {e}"
