from datetime import datetime

from models import pedido_model
from services import clientes_http
from services.clientes_http import StockInsuficienteError


class ValidacionError(Exception):
    pass


class ProductoNoEncontradoError(Exception):
    pass


def _validar_payload(carne_integrante, items):
    if not carne_integrante or not carne_integrante.strip():
        raise ValidacionError("El carné del integrante que crea el pedido es obligatorio")
    if not items or not isinstance(items, list):
        raise ValidacionError("El pedido debe incluir al menos un item")
    for item in items:
        if "sku" not in item or "cantidad" not in item:
            raise ValidacionError("Cada item requiere 'sku' y 'cantidad'")
        if int(item["cantidad"]) <= 0:
            raise ValidacionError(f"La cantidad de '{item.get('sku')}' debe ser mayor a 0")


def crear_pedido(carne_integrante, cliente_id, items):
    """Flujo completo de creación de un pedido:

    1. Trae el precio real de cada producto desde 'catalogo' (nunca se confía
       en el precio que venga del cliente/frontend).
    2. Pide a 'inventario' que descuente el stock de forma atómica — si algún
       producto no alcanza, TODO el pedido se rechaza y nada se descuenta.
    3. Si el descuento fue exitoso, guarda el pedido en la base de 'pedidos'.
    4. Si el paso 3 falla (por ejemplo la BD de pedidos cae justo en ese
       instante), se compensa devolviendo el stock ya descontado en el
       paso 2 — patrón saga, porque no hay una transacción distribuida real
       entre bases de datos de microservicios distintos.
    """
    _validar_payload(carne_integrante, items)

    items_con_precio = []
    total = 0
    for item in items:
        producto = clientes_http.obtener_producto(item["sku"])
        if producto is None:
            raise ProductoNoEncontradoError(f"El producto '{item['sku']}' no existe en catálogo")
        precio_unitario = float(producto["precio"])
        cantidad = int(item["cantidad"])
        items_con_precio.append(
            {"sku": item["sku"], "cantidad": cantidad, "precio_unitario": precio_unitario}
        )
        total += precio_unitario * cantidad

    items_para_stock = [{"sku": i["sku"], "cantidad": i["cantidad"]} for i in items_con_precio]

    # Paso 2: descuento atómico en inventario (todo o nada)
    clientes_http.descontar_stock(items_para_stock)

    # Paso 3: guardar el pedido; si falla, compensar el stock (paso 4)
    try:
        return pedido_model.crear_pedido_con_items(
            carne_integrante, cliente_id, items_con_precio, round(total, 2)
        )
    except Exception:
        clientes_http.incrementar_stock(items_para_stock)
        raise


def _validar_fecha(nombre_campo, valor):
    if valor is None:
        return None
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        raise ValidacionError(f"'{nombre_campo}' debe tener formato YYYY-MM-DD")
    return valor


def listar_pedidos(desde=None, hasta=None, cliente_id=None, skus=None):
    desde = _validar_fecha("desde", desde)
    hasta = _validar_fecha("hasta", hasta)
    if desde and hasta and desde > hasta:
        raise ValidacionError("'desde' no puede ser posterior a 'hasta'")
    return pedido_model.obtener_filtrados(
        desde=desde, hasta=hasta, cliente_id=cliente_id, skus=skus
    )


def obtener_pedido(pedido_id):
    pedido = pedido_model.obtener_por_id(pedido_id)
    if pedido is None:
        raise KeyError(f"No existe el pedido con id {pedido_id}")
    return pedido
