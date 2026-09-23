from flask import jsonify, request
from services import pedido_service
from services.pedido_service import ValidacionError, ProductoNoEncontradoError
from services.clientes_http import StockInsuficienteError


def crear():
    datos = request.get_json(silent=True) or {}
    try:
        pedido = pedido_service.crear_pedido(
            carne_integrante=datos.get("carne_integrante"),
            cliente_id=datos.get("cliente_id"),
            items=datos.get("items"),
        )
        return jsonify(pedido), 201
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400
    except ProductoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404
    except StockInsuficienteError as e:
        return jsonify({"error": "Stock insuficiente", "detalle": e.detalle}), 409


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

    try:
        pedidos = pedido_service.listar_pedidos(
            desde=desde, hasta=hasta, cliente_id=cliente_id, skus=skus
        )
        return jsonify(pedidos), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400


def obtener(pedido_id):
    try:
        return jsonify(pedido_service.obtener_pedido(pedido_id)), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
