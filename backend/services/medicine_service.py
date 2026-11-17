"""
Modulo de compatibilidad. Redirige a product_service ya que el catalogo
abarca todos los productos comerciales de la farmacia.
"""
from backend.services.product_service import (
    get_all_products,
    search_products,
    get_product_by_id,
    get_product_by_folio,
    create_product,
    update_product,
    delete_product,
    get_providers_list
)
