from flask import Blueprint
from controllers import reporte_controller

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")

reportes_bp.route("/ventas", methods=["GET"])(reporte_controller.ventas)
reportes_bp.route("/clientes", methods=["GET"])(reporte_controller.clientes)
reportes_bp.route("/productos", methods=["GET"])(reporte_controller.productos)
