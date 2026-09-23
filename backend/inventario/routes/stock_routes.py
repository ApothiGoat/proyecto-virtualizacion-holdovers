from flask import Blueprint
from controllers import stock_controller

stock_bp = Blueprint("stock", __name__, url_prefix="/stock")

stock_bp.route("", methods=["GET"])(stock_controller.listar)
stock_bp.route("/<string:sku>", methods=["GET"])(stock_controller.obtener)
stock_bp.route("/<string:sku>", methods=["PUT"])(stock_controller.fijar)
stock_bp.route("/descontar", methods=["POST"])(stock_controller.descontar)
stock_bp.route("/incrementar", methods=["POST"])(stock_controller.incrementar)
