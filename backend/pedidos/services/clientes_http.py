"""Llamadas HTTP a otros microservicios (comunicación por nombre de servicio
en la red interna de Docker Compose, p. ej. http://catalogo:5000)."""
import os
import requests

CATALOGO_URL = os.environ.get("CATALOGO_URL", "http://catalogo:5000")
INVENTARIO_URL = os.environ.get("INVENTARIO_URL", "http://inventario:5000")

TIMEOUT = 5  # segundos


def obtener_producto(sku):
    resp = requests.get(f"{CATALOGO_URL}/productos/{sku}", timeout=TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def descontar_stock(items):
    """items: [{"sku":..., "cantidad":...}]. Lanza StockInsuficienteError si falla."""
    resp = requests.post(
        f"{INVENTARIO_URL}/stock/descontar", json={"items": items}, timeout=TIMEOUT
    )
    if resp.status_code == 409:
        raise StockInsuficienteError(resp.json().get("detalle", []))
    resp.raise_for_status()


def incrementar_stock(items):
    """Compensación (saga) — repone stock si falla el guardado del pedido."""
    resp = requests.post(
        f"{INVENTARIO_URL}/stock/incrementar", json={"items": items}, timeout=TIMEOUT
    )
    resp.raise_for_status()


class StockInsuficienteError(Exception):
    def __init__(self, detalle):
        self.detalle = detalle
        super().__init__("; ".join(detalle))
