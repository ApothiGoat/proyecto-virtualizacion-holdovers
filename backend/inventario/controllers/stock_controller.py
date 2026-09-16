from flask import jsonify, request
from services import stock_service
from services.stock_service import ValidacionError, StockInsuficienteError


def listar():
    return jsonify(stock_service.listar_stock()), 200


def obtener(sku):
    try:
        return jsonify(stock_service.obtener_stock(sku)), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


def fijar(sku):
    datos = request.get_json(silent=True) or {}
    try:
        fila = stock_service.fijar_stock(sku, datos.get("cantidad"))
        return jsonify(fila), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400


def descontar():
    """POST /stock/descontar  body: {"items": [{"sku": "...", "cantidad": N}, ...]}

    Todo o nada: si un solo producto no alcanza, no se descuenta ningún item.
    Este es el endpoint que llama 'pedidos' al confirmar una orden.
    """
    datos = request.get_json(silent=True) or {}
    items = datos.get("items")
    try:
        stock_service.descontar_stock(items)
        return jsonify({"mensaje": "Stock descontado correctamente"}), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400
    except StockInsuficienteError as e:
        return jsonify({"error": "Stock insuficiente", "detalle": e.errores}), 409


def incrementar():
    """POST /stock/incrementar — compensación (saga), no expuesta al usuario final."""
    datos = request.get_json(silent=True) or {}
    items = datos.get("items")
    try:
        stock_service.incrementar_stock(items)
        return jsonify({"mensaje": "Stock repuesto correctamente"}), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400
