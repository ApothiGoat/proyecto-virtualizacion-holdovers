from flask import jsonify, request
from services import reporte_service
from services.reporte_service import ValidacionError


def ventas():
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")
    try:
        return jsonify(reporte_service.reporte_ventas(desde, hasta)), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400


def clientes():
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")
    cliente_id = request.args.get("cliente_id", type=int)
    try:
        return jsonify(reporte_service.reporte_clientes(desde, hasta, cliente_id)), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400


def productos():
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")
    sku_param = request.args.get("sku")
    skus = [s.strip() for s in sku_param.split(",") if s.strip()] if sku_param else None
    try:
        return jsonify(reporte_service.reporte_productos(desde, hasta, skus)), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400
