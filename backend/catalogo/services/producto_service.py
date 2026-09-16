from models import producto_model


class ValidacionError(Exception):
    """Error de validación de negocio (se traduce a 400 en el controller)."""


def _validar_datos(sku, nombre, categoria, precio):
    if not sku or not sku.strip():
        raise ValidacionError("El SKU es obligatorio")
    if not nombre or not nombre.strip():
        raise ValidacionError("El nombre es obligatorio")
    if precio is None or float(precio) <= 0:
        raise ValidacionError("El precio debe ser mayor a 0")


def listar_productos():
    return producto_model.obtener_todos()


def obtener_producto(sku):
    producto = producto_model.obtener_por_sku(sku)
    if producto is None:
        raise KeyError(f"No existe un producto con SKU '{sku}'")
    return producto


def crear_producto(sku, nombre, categoria, precio):
    _validar_datos(sku, nombre, categoria, precio)
    if producto_model.obtener_por_sku(sku) is not None:
        raise ValidacionError(f"Ya existe un producto con SKU '{sku}'")
    return producto_model.crear(sku, nombre, categoria, precio)


def actualizar_producto(sku, nombre, categoria, precio):
    _validar_datos(sku, nombre, categoria, precio)
    actualizado = producto_model.actualizar(sku, nombre, categoria, precio)
    if actualizado is None:
        raise KeyError(f"No existe un producto con SKU '{sku}'")
    return actualizado


def eliminar_producto(sku):
    eliminado = producto_model.eliminar(sku)
    if eliminado is None:
        raise KeyError(f"No existe un producto con SKU '{sku}'")
    return eliminado
