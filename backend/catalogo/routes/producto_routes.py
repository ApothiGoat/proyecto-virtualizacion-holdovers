from flask import Blueprint
from controllers import producto_controller

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")

productos_bp.route("", methods=["GET"])(producto_controller.listar)
productos_bp.route("", methods=["POST"])(producto_controller.crear)

# /categorias va antes que /<sku>; Flask igual prioriza la ruta fija sobre la variable
productos_bp.route("/categorias", methods=["GET"])(producto_controller.listar_categorias)
productos_bp.route("/categorias", methods=["POST"])(producto_controller.crear_categoria)

productos_bp.route("/<string:sku>", methods=["GET"])(producto_controller.obtener)
productos_bp.route("/<string:sku>", methods=["PUT"])(producto_controller.actualizar)
productos_bp.route("/<string:sku>", methods=["DELETE"])(producto_controller.eliminar)