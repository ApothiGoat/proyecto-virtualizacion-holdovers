from models import stock_model


class ValidacionError(Exception):
    pass


class StockInsuficienteError(Exception):
    def __init__(self, errores):
        self.errores = errores
        super().__init__("; ".join(errores))


def listar_stock():
    return stock_model.obtener_todos()


def obtener_stock(sku):
    fila = stock_model.obtener_por_sku(sku)
    if fila is None:
        raise KeyError(f"No hay registro de stock para SKU '{sku}'")
    return fila


def fijar_stock(sku, cantidad):
    if not sku or not sku.strip():
        raise ValidacionError("El SKU es obligatorio")
    if cantidad is None or int(cantidad) < 0:
        raise ValidacionError("La cantidad debe ser un entero mayor o igual a 0")
    return stock_model.upsert_stock(sku, int(cantidad))


def _validar_items(items):
    if not items or not isinstance(items, list):
        raise ValidacionError("Se requiere una lista de items no vacía")
    for item in items:
        if "sku" not in item or "cantidad" not in item:
            raise ValidacionError("Cada item requiere 'sku' y 'cantidad'")
        if int(item["cantidad"]) <= 0:
            raise ValidacionError(f"La cantidad de '{item.get('sku')}' debe ser mayor a 0")


def descontar_stock(items):
    """Punto de entrada usado por 'pedidos' para el descuento atómico."""
    _validar_items(items)
    exito, errores = stock_model.descontar_atomico(items)
    if not exito:
        raise StockInsuficienteError(errores)


def incrementar_stock(items):
    """Compensación — usada por 'pedidos' si falla el paso posterior a descontar."""
    _validar_items(items)
    stock_model.incrementar_atomico(items)
