from flask import Blueprint
from controllers import cliente_controller

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

clientes_bp.route("", methods=["GET"])(cliente_controller.listar)
clientes_bp.route("/<int:cliente_id>", methods=["GET"])(cliente_controller.obtener)
clientes_bp.route("", methods=["POST"])(cliente_controller.crear)
clientes_bp.route("/<int:cliente_id>", methods=["PUT"])(cliente_controller.actualizar)
clientes_bp.route("/<int:cliente_id>", methods=["DELETE"])(cliente_controller.eliminar)
