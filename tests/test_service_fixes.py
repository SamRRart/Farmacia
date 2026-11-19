import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from backend.services import client_service, mail_service, purchase_service, report_service, sale_service, user_service
from backend.services.product_service import assign_product_provider, generate_default_folio
from frontend.interfaces.reports_view import ReportsView


class FakeCursor:
    def __init__(self, fetchone_results=None, fetchall_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class ServiceFixTests(unittest.TestCase):
    def test_generated_folio_uses_highest_existing_number(self):
        cursor = FakeCursor(fetchall_results=[[
            ("MED-001",),
            ("MED-003",),
            ("MED-OTHER",)
        ]])

        self.assertEqual(generate_default_folio("Medicamento", cursor), "MED-004")

    def test_existing_product_can_be_assigned_to_a_valid_provider(self):
        cursor = FakeCursor(fetchone_results=[(7,), (3,)])
        connection = FakeConnection(cursor)

        with patch("backend.services.product_service.get_connection", return_value=connection):
            success, message = assign_product_provider(7, 3)

        self.assertTrue(success)
        self.assertIn("asignado", message)
        self.assertIn("UPDATE Productos SET id_proveedor", cursor.executed[-1][0])
        self.assertEqual(connection.commits, 1)

    def test_duplicate_client_rfc_is_rejected_before_insert(self):
        cursor = FakeCursor(fetchone_results=[(12,)])
        connection = FakeConnection(cursor)

        with patch.object(client_service, "get_connection", return_value=connection):
            result = client_service.create_client("Ana", "123", "abc123", "", None)

        self.assertFalse(result)
        self.assertEqual(len(cursor.executed), 1)
        self.assertIn("SELECT id_cliente", cursor.executed[0][0])
        self.assertEqual(connection.commits, 0)

    def test_existing_duplicate_rfc_is_not_resolved_to_an_arbitrary_client(self):
        cursor = FakeCursor(fetchall_results=[[
            (12, "Ana", "123", "ABC123", "", None, 0, "", ""),
            (13, "Ana duplicada", "456", "ABC123", "", None, 50, "", "")
        ]])
        connection = FakeConnection(cursor)

        with patch.object(sale_service, "get_connection", return_value=connection):
            with self.assertRaisesRegex(ValueError, "varios clientes"):
                sale_service.get_client_by_rfc("ABC123")

    def test_last_admin_cannot_be_deleted(self):
        cursor = FakeCursor(fetchone_results=[("Admin", "Admin"), (1,)])
        connection = FakeConnection(cursor)

        with patch.object(user_service, "get_connection", return_value=connection):
            success, message = user_service.delete_user(1)

        self.assertFalse(success)
        self.assertIn("unico administrador", message)
        self.assertFalse(any("DELETE FROM Usuarios" in query for query, _ in cursor.executed))

    def test_restock_rejects_product_without_provider(self):
        cursor = FakeCursor(fetchone_results=[(7, None, "Producto sin proveedor", 15.0)])
        connection = FakeConnection(cursor)

        with patch.object(purchase_service, "get_connection", return_value=connection):
            success, message, purchase_ids = purchase_service.create_restock_orders(
                [{"id_producto": 7, "cantidad": 2}],
                id_usuario=1
            )

        self.assertFalse(success)
        self.assertIn("no tiene proveedor asignado", message)
        self.assertEqual(purchase_ids, [])
        self.assertFalse(any("INSERT INTO Compras" in query for query, _ in cursor.executed))
        self.assertEqual(connection.commits, 0)

    def test_invalid_or_reversed_report_dates_raise(self):
        with self.assertRaises(ValueError):
            report_service.parse_date_boundary("2025-02-30")

        with self.assertRaises(ValueError):
            report_service._parse_date_range("2025-05-02", "2025-05-01")

    def test_report_end_boundary_includes_the_whole_day(self):
        self.assertEqual(
            report_service.parse_date_boundary("2025-05-01", is_end=True),
            "2025-05-02 00:00:00"
        )

    def test_sales_report_uses_exclusive_end_boundary(self):
        cursor = FakeCursor(fetchall_results=[[]])
        connection = FakeConnection(cursor)

        with patch.object(report_service, "get_connection", return_value=connection):
            report_service.get_sales_by_date_range("2025-05-01", "2025-05-01")

        query, params = cursor.executed[0]
        self.assertIn("v.fecha_hora < %s", query)
        self.assertEqual(params, ("2025-05-01 00:00:00", "2025-05-02 00:00:00"))

    def test_switching_report_state_clears_previous_export_data(self):
        view = SimpleNamespace(
            _current_rows=[{"id": 1}],
            _current_kpis={"total_registros": 1},
            _current_headers=["ID"],
            _current_col_keys=["id"],
            _render_kpis=Mock()
        )

        ReportsView._reset_report_state(view)

        self.assertEqual(view._current_rows, [])
        self.assertEqual(view._current_kpis, {})
        self.assertEqual(view._current_headers, [])
        self.assertEqual(view._current_col_keys, [])

    def test_restock_email_without_smtp_credentials_is_not_reported_as_sent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "order.pdf"
            pdf_path.write_bytes(b"%PDF-1.0")

            with patch.object(mail_service, "check_internet_connection", return_value=True), \
                    patch.object(mail_service, "get_smtp_config", return_value={
                        "server": "smtp.example.com",
                        "port": 587,
                        "user": "",
                        "password": "",
                        "sender": "Farmacia <no-reply@example.com>"
                    }):
                sent, message = mail_service.send_restock_order_email(
                    "provider@example.com",
                    "Proveedor",
                    9,
                    [],
                    100.0
                )

        self.assertFalse(sent)
        self.assertIn("faltan las credenciales SMTP", message)

    def test_invoice_email_without_smtp_credentials_is_not_reported_as_sent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "invoice.pdf"
            pdf_path.write_bytes(b"%PDF-1.0")

            with patch.object(mail_service, "check_internet_connection", return_value=True), \
                    patch.object(mail_service, "get_smtp_config", return_value={
                        "server": "smtp.example.com",
                        "port": 587,
                        "user": "",
                        "password": "",
                        "sender": "Farmacia <no-reply@example.com>"
                    }):
                sent, message = mail_service.send_invoice_email(
                    "client@example.com",
                    "Cliente",
                    "RFC123",
                    str(pdf_path),
                    100.0
                )

        self.assertFalse(sent)
        self.assertIn("faltan las credenciales SMTP", message)

    def test_restock_email_sends_using_configured_smtp(self):
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp.__exit__.return_value = False
        smtp_config = {
            "server": "smtp.example.com",
            "port": 587,
            "user": "sender@example.com",
            "password": "test-password",
            "sender": "Farmacia <sender@example.com>"
        }

        with patch.object(mail_service, "check_internet_connection", return_value=True), \
                patch.object(mail_service, "get_smtp_config", return_value=smtp_config), \
                patch.object(mail_service.smtplib, "SMTP", return_value=smtp):
            sent, message = mail_service.send_restock_order_email(
                "provider@example.com",
                "Proveedor",
                9,
                [{"nombre": "Producto", "cantidad": 2}],
                100.0
            )

        self.assertTrue(sent)
        self.assertIn("notificada exitosamente", message)
        smtp.send_message.assert_called_once()

    def test_invalid_smtp_config_is_reported_instead_of_escaping(self):
        with patch.object(mail_service, "check_internet_connection", return_value=True), \
                patch.object(mail_service, "get_smtp_config", side_effect=ValueError("invalid SMTP port")):
            sent, message = mail_service.send_restock_order_email(
                "provider@example.com",
                "Proveedor",
                9,
                [],
                100.0
            )

        self.assertFalse(sent)
        self.assertIn("invalid SMTP port", message)


if __name__ == "__main__":
    unittest.main()
