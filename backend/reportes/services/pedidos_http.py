"""Cliente HTTP hacia el microservicio 'pedidos' — reportes no tiene base de
datos propia, agrega datos que ya viven en pedidos y clientes."""
import os
import requests

PEDIDOS_URL = os.environ.get("PEDIDOS_URL", "http://pedidos:5000")
TIMEOUT = 10

# Solo las ventas cerradas cuentan en los reportes: un pedido 'pendiente'
# todavía no es venta y uno 'cancelado' nunca lo fue.
ESTADO_VENTA = "completado"


def listar_pedidos(desde=None, hasta=None, cliente_id=None, skus=None):
    params = {}
    if desde:
        params["desde"] = desde
    if hasta:
        params["hasta"] = hasta
    if cliente_id is not None:
        params["cliente_id"] = cliente_id
    if skus:
        params["sku"] = ",".join(skus)

    resp = requests.get(f"{PEDIDOS_URL}/pedidos", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return [p for p in resp.json() if p.get("estado") == ESTADO_VENTA]