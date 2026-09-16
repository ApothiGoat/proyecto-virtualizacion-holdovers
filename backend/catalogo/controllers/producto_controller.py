from flask import jsonify, request
from services import producto_service
from services.producto_service import ValidacionError


def listar():
    productos = producto_service.listar_productos()
    return jsonify(productos), 200


def obtener(sku):
    try:
        producto = producto_service.obtener_producto(sku)
        return jsonify(producto), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


def crear():
    datos = request.get_json(silent=True) or {}
    try:
        producto = producto_service.crear_producto(
            sku=datos.get("sku"),
            nombre=datos.get("nombre"),
            categoria=datos.get("categoria"),
            precio=datos.get("precio"),
        )
        return jsonify(producto), 201
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400


def actualizar(sku):
    datos = request.get_json(silent=True) or {}
    try:
        producto = producto_service.actualizar_producto(
            sku=sku,
            nombre=datos.get("nombre"),
            categoria=datos.get("categoria"),
            precio=datos.get("precio"),
        )
        return jsonify(producto), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


def eliminar(sku):
    try:
        eliminado = producto_service.eliminar_producto(sku)
        return jsonify({"mensaje": f"Producto {eliminado['sku']} eliminado"}), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
