from flask import jsonify, request
from services import cliente_service
from services.cliente_service import ValidacionError


def listar():
    return jsonify(cliente_service.listar_clientes()), 200


def obtener(cliente_id):
    try:
        return jsonify(cliente_service.obtener_cliente(cliente_id)), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


def crear():
    datos = request.get_json(silent=True) or {}
    try:
        cliente = cliente_service.crear_cliente(
            nombre=datos.get("nombre"),
            email=datos.get("email"),
            telefono=datos.get("telefono"),
        )
        return jsonify(cliente), 201
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400


def actualizar(cliente_id):
    datos = request.get_json(silent=True) or {}
    try:
        cliente = cliente_service.actualizar_cliente(
            cliente_id=cliente_id,
            nombre=datos.get("nombre"),
            email=datos.get("email"),
            telefono=datos.get("telefono"),
        )
        return jsonify(cliente), 200
    except ValidacionError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


def eliminar(cliente_id):
    try:
        cliente_service.eliminar_cliente(cliente_id)
        return jsonify({"mensaje": f"Cliente {cliente_id} eliminado"}), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
