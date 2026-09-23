from flask import Blueprint
from controllers import producto_controller

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")

productos_bp.route("", methods=["GET"])(producto_controller.listar)
productos_bp.route("/<string:sku>", methods=["GET"])(producto_controller.obtener)
productos_bp.route("", methods=["POST"])(producto_controller.crear)
productos_bp.route("/<string:sku>", methods=["PUT"])(producto_controller.actualizar)
productos_bp.route("/<string:sku>", methods=["DELETE"])(producto_controller.eliminar)
