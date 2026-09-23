from flask import Blueprint
from controllers import pedido_controller

pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")

pedidos_bp.route("", methods=["POST"])(pedido_controller.crear)
pedidos_bp.route("", methods=["GET"])(pedido_controller.listar)
pedidos_bp.route("/<int:pedido_id>", methods=["GET"])(pedido_controller.obtener)
