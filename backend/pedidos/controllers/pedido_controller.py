import requests
from flask import jsonify, request

from services import pedido_service
from services.pedido_service import (
    EstadoInvalidoError,
    ProductoNoEncontradoError,
    ServicioExternoError,
    ValidacionError,
)
from services.clientes_http import StockInsuficienteError


def _error_http(e):
    """Traduce las excepciones del servicio a respuestas HTTP.
    Devuelve None si la excepción no es una de las conocidas."""
    if isinstance(e, ValidacionError):
        return jsonify({"error": str(e)}), 400
    if isinstance(e, ProductoNoEncontradoError):
        return jsonify({"error": str(e)}), 404
    if isinstance(e, KeyError):
        return jsonify({"error": e.args[0] if e.args else "No encontrado"}), 404
    if isinstance(e, EstadoInvalidoError):
        return jsonify({"error": str(e)}), 409
    if isinstance(e, StockInsuficienteError):
        return jsonify({"error": f"Stock insuficiente: {e}", "detalle": e.detalle}), 409
    if isinstance(e, ServicioExternoError):
        return jsonify({"error": str(e)}), 502
    if isinstance(e, requests.exceptions.RequestException):
        return jsonify({"error": "No se pudo comunicar con otro servicio (catálogo o inventario)"}), 502
    return None


def _responder(accion, codigo_ok=200):
    try:
        return jsonify(accion()), codigo_ok
    except Exception as e:
        respuesta = _error_http(e)
        if respuesta is None:
            raise
        return respuesta


def crear():
    datos = request.get_json(silent=True) or {}
    return _responder(
        lambda: pedido_service.crear_pedido(
            carne_integrante=datos.get("carne_integrante"),
            cliente_id=datos.get("cliente_id"),
            items=datos.get("items"),
        ),
        201,
    )


def listar():
    """GET /pedidos?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&cliente_id=N&sku=A,B

    Todos los filtros son opcionales. 'sku' acepta uno o varios SKUs
    separados por coma. Sin filtros, devuelve todos los pedidos.
    Usado directamente por el frontend/admin y también por 'reportes'.
    """
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")
    cliente_id = request.args.get("cliente_id", type=int)
    sku_param = request.args.get("sku")
    skus = [s.strip() for s in sku_param.split(",") if s.strip()] if sku_param else None

    return _responder(
        lambda: pedido_service.listar_pedidos(
            desde=desde, hasta=hasta, cliente_id=cliente_id, skus=skus
        )
    )


def obtener(pedido_id):
    return _responder(lambda: pedido_service.obtener_pedido(pedido_id))


def editar(pedido_id):
    """PUT /pedidos/<id>  body: {cliente_id, items:[{sku, cantidad}]}  (solo pendientes)"""
    datos = request.get_json(silent=True) or {}
    return _responder(
        lambda: pedido_service.editar_pedido(
            pedido_id,
            cliente_id=datos.get("cliente_id"),
            items=datos.get("items"),
        )
    )


def cambiar_estado(pedido_id):
    """PATCH /pedidos/<id>/estado  body: {estado: 'completado' | 'cancelado'}"""
    datos = request.get_json(silent=True) or {}
    return _responder(
        lambda: pedido_service.cambiar_estado(pedido_id, datos.get("estado"))
    )