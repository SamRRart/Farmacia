"""
Modelo y Gestor de Reportes del Sistema Farmacia CUCEI.
Basado en el Diagrama de Clases unificado de Farmacia CUCEI (GestorReportes).
"""

from typing import Optional, List, Dict, Any, Tuple

class GestorReportes:
    """
    Gestor que centraliza la logica de generacion y presentacion de reportes
    gerenciales y analisis de transacciones (Ventas, Compras, Clientes y Facturacion).
    Cumple estrictamente con la interfaz definida en el Diagrama de Clases del sistema.
    """

    def __init__(self):
        pass

    @classmethod
    def generarReporteClientesPorUbicacion(
        cls,
        filtro: Optional[str] = None,
        ciudad: Optional[str] = None,
        estado: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Consulta y estructura el reporte de clientes filtrados por ciudad y/o estado.
        Acepta un filtro libre (busca en ciudad, estado y nombre) o bien
        parametros especificos ciudad= / estado=.
        Retorna: (lista_registros, resumen_kpis)
        """
        from backend.services.report_service import get_clients_by_location
        return get_clients_by_location(filtro=filtro, ciudad=ciudad, estado=estado)

    @classmethod
    def generarReporteVentasPorFecha(
        cls, 
        inicio: Optional[str] = None, 
        fin: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Consulta y estructura el reporte de ventas realizadas dentro de un periodo de fechas.
        Retorna: (lista_registros, resumen_kpis)
        """
        from backend.services.report_service import get_sales_by_date_range
        return get_sales_by_date_range(fecha_inicio=inicio, fecha_fin=fin)

    @classmethod
    def generarReporteComprasPorFecha(
        cls, 
        inicio: Optional[str] = None, 
        fin: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Consulta y estructura el reporte de compras a proveedores en un periodo de fechas.
        Retorna: (lista_registros, resumen_kpis)
        """
        from backend.services.report_service import get_purchases_by_date_range
        return get_purchases_by_date_range(fecha_inicio=inicio, fecha_fin=fin)

    @classmethod
    def generarReporteFacturasMayorVenta(
        cls, 
        limite: int = 20, 
        monto_minimo: float = 0.0
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Consulta y estructura las facturas asociadas a las ventas con mayores importes.
        Retorna: (lista_registros, resumen_kpis)
        """
        from backend.services.report_service import get_invoices_by_highest_sales
        return get_invoices_by_highest_sales(limite=limite, monto_minimo=monto_minimo)
