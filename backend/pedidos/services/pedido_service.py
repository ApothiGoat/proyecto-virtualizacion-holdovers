import logging
from datetime import datetime

from models import pedido_model
from services import clientes_http
from services.clientes_http import StockInsuficienteError

logger = logging.getLogger(__name__)

ESTADOS_DESTINO = ("completado", "cancelado")


class ValidacionError(Exception):
    pass


class ProductoNoEncontradoError(Exception):
    pass


class EstadoInvalidoError(Exception):
    """El pedido ya no está 'pendiente', así que no admite el cambio."""


class ServicioExternoError(Exception):
    """Otro microservicio falló después de que el cambio ya se había guardado."""


# ---------------------------------------------------------------- validaciones

def _validar_items(items):
    if not items or not isinstance(items, list):
        raise ValidacionError("El pedido debe incluir al menos un item")
    for item in items:
        if not isinstance(item, dict) or "sku" not in item or "cantidad" not in item:
            raise ValidacionError("Cada item requiere 'sku' y 'cantidad'")
        try:
            cantidad = int(item["cantidad"])
        except (TypeError, ValueError):
            raise ValidacionError(f"La cantidad de '{item.get('sku')}' debe ser un número entero")
        if cantidad <= 0:
            raise ValidacionError(f"La cantidad de '{item.get('sku')}' debe ser mayor a 0")


def _validar_payload(carne_integrante, items):
    if not carne_integrante or not carne_integrante.strip():
        raise ValidacionError("El carné del integrante que crea el pedido es obligatorio")
    _validar_items(items)


def _normalizar_cliente_id(cliente_id):
    if cliente_id is None or cliente_id == "":
        return None
    try:
        return int(cliente_id)
    except (TypeError, ValueError):
        raise ValidacionError("'cliente_id' debe ser un número entero")


# --------------------------------------------------------------------- helpers

def _consolidar_items(items):
    """Suma cantidades si el mismo SKU aparece en varias líneas. Devuelve {sku: cantidad}."""
    por_sku = {}
    for item in items:
        por_sku[item["sku"]] = por_sku.get(item["sku"], 0) + int(item["cantidad"])
    return por_sku


def _precios_y_total(por_sku):
    """Trae el precio real de cada producto desde 'catalogo' (nunca se confía
    en el precio que venga del frontend). Devuelve (items_con_precio, total)."""
    items_con_precio = []
    total = 0
    for sku, cantidad in por_sku.items():
        producto = clientes_http.obtener_producto(sku)
        if producto is None:
            raise ProductoNoEncontradoError(f"El producto '{sku}' no existe en catálogo")
        precio_unitario = float(producto["precio"])
        items_con_precio.append(
            {"sku": sku, "cantidad": cantidad, "precio_unitario": precio_unitario}
        )
        total += precio_unitario * cantidad
    return items_con_precio, round(total, 2)


def _compensar_stock(items_para_stock):
    """Repone stock ya descontado cuando algo falla después. Nunca lanza: si la
    compensación también falla se registra, para no tapar el error original."""
    if not items_para_stock:
        return
    try:
        clientes_http.incrementar_stock(items_para_stock)
    except Exception:
        logger.exception("No se pudo compensar el stock: %s", items_para_stock)


def _devolver_stock(items_para_stock):
    """Devuelve stock a inventario cuando el cambio en pedidos YA se guardó."""
    if not items_para_stock:
        return
    try:
        clientes_http.incrementar_stock(items_para_stock)
    except Exception:
        logger.exception("No se pudo devolver el stock: %s", items_para_stock)
        raise ServicioExternoError(
            "El cambio se guardó, pero no se pudo devolver el stock a inventario. "
            "Ajústalo manualmente en Inventario."
        )


def _stock_de_items(items):
    """Items de un pedido guardado -> [{'sku', 'cantidad'}] consolidado."""
    por_sku = _consolidar_items(items)
    return [{"sku": sku, "cantidad": cant} for sku, cant in por_sku.items()]


# ----------------------------------------------------------------------- casos

def crear_pedido(carne_integrante, cliente_id, items):
    """Flujo completo de creación de un pedido:

    1. Trae el precio real de cada producto desde 'catalogo'.
    2. Pide a 'inventario' que descuente el stock de forma atómica — si algún
       producto no alcanza, TODO el pedido se rechaza y nada se descuenta.
    3. Si el descuento fue exitoso, guarda el pedido (estado 'pendiente').
    4. Si el paso 3 falla, se compensa devolviendo el stock ya descontado —
       patrón saga, porque no hay transacción distribuida entre bases de datos
       de microservicios distintos.
    """
    _validar_payload(carne_integrante, items)
    cliente_id = _normalizar_cliente_id(cliente_id)

    items_con_precio, total = _precios_y_total(_consolidar_items(items))
    items_para_stock = [{"sku": i["sku"], "cantidad": i["cantidad"]} for i in items_con_precio]

    clientes_http.descontar_stock(items_para_stock)

    try:
        return pedido_model.crear_pedido_con_items(
            carne_integrante, cliente_id, items_con_precio, total
        )
    except Exception:
        _compensar_stock(items_para_stock)
        raise


def editar_pedido(pedido_id, cliente_id, items):
    """Edita cliente e ítems de un pedido PENDIENTE.

    Los precios se recalculan con el catálogo actual (el pedido todavía no es
    una venta). El stock se ajusta solo por la diferencia contra lo que el
    pedido ya tenía reservado.
    """
    _validar_items(items)
    cliente_id = _normalizar_cliente_id(cliente_id)

    actual = obtener_pedido(pedido_id)
    if actual["estado"] != "pendiente":
        raise EstadoInvalidoError("Solo se pueden editar pedidos pendientes")

    nuevo = _consolidar_items(items)
    viejo = _consolidar_items(actual["items"])
    items_con_precio, total = _precios_y_total(nuevo)

    a_descontar = [
        {"sku": sku, "cantidad": cant - viejo.get(sku, 0)}
        for sku, cant in nuevo.items()
        if cant > viejo.get(sku, 0)
    ]
    a_devolver = [
        {"sku": sku, "cantidad": cant - nuevo.get(sku, 0)}
        for sku, cant in viejo.items()
        if cant > nuevo.get(sku, 0)
    ]

    if a_descontar:
        clientes_http.descontar_stock(a_descontar)  # StockInsuficienteError => nada cambia

    try:
        actualizado = pedido_model.reemplazar_pedido(
            pedido_id, cliente_id, items_con_precio, total
        )
    except Exception:
        _compensar_stock(a_descontar)
        raise

    if actualizado is None:
        # alguien lo cerró/canceló entre la lectura y el guardado
        _compensar_stock(a_descontar)
        raise EstadoInvalidoError("El pedido ya no está pendiente")

    _devolver_stock(a_devolver)
    return actualizado


def cambiar_estado(pedido_id, nuevo_estado):
    """pendiente -> completado (venta) | cancelado (repone el stock)."""
    if nuevo_estado not in ESTADOS_DESTINO:
        raise ValidacionError("'estado' debe ser 'completado' o 'cancelado'")

    actual = obtener_pedido(pedido_id)
    if actual["estado"] != "pendiente":
        raise EstadoInvalidoError(
            f"El pedido {pedido_id} ya está '{actual['estado']}' y no se puede modificar"
        )

    actualizado = pedido_model.cambiar_estado(pedido_id, nuevo_estado)
    if actualizado is None:
        raise EstadoInvalidoError("El pedido ya no está pendiente")

    if nuevo_estado == "cancelado":
        _devolver_stock(_stock_de_items(actualizado["items"]))

    return actualizado


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