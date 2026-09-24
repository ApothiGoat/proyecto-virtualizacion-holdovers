from models import producto_model


class ValidacionError(Exception):
    """Error de validación de negocio (se traduce a 400 en el controller)."""


def _validar_datos(sku, nombre, categoria, precio):
    """Valida los datos y devuelve la categoría tal como está guardada en el
    catálogo (así 'electrónica' se normaliza a 'Electrónica')."""
    if not sku or not sku.strip():
        raise ValidacionError("El SKU es obligatorio")
    if not nombre or not nombre.strip():
        raise ValidacionError("El nombre es obligatorio")
    if precio is None or float(precio) <= 0:
        raise ValidacionError("El precio debe ser mayor a 0")
    if not categoria or not categoria.strip():
        raise ValidacionError("La categoría es obligatoria")

    existente = producto_model.obtener_categoria(categoria.strip())
    if existente is None:
        raise ValidacionError(
            f"La categoría '{categoria.strip()}' no existe en el catálogo. "
            "Créala primero con el botón +"
        )
    return existente["nombre"]


def listar_productos():
    return producto_model.obtener_todos()


def obtener_producto(sku):
    producto = producto_model.obtener_por_sku(sku)
    if producto is None:
        raise KeyError(f"No existe un producto con SKU '{sku}'")
    return producto


def crear_producto(sku, nombre, categoria, precio):
    categoria = _validar_datos(sku, nombre, categoria, precio)
    if producto_model.obtener_por_sku(sku) is not None:
        raise ValidacionError(f"Ya existe un producto con SKU '{sku}'")
    return producto_model.crear(sku, nombre, categoria, precio)


def actualizar_producto(sku, nombre, categoria, precio):
    categoria = _validar_datos(sku, nombre, categoria, precio)
    actualizado = producto_model.actualizar(sku, nombre, categoria, precio)
    if actualizado is None:
        raise KeyError(f"No existe un producto con SKU '{sku}'")
    return actualizado


def eliminar_producto(sku):
    eliminado = producto_model.eliminar(sku)
    if eliminado is None:
        raise KeyError(f"No existe un producto con SKU '{sku}'")
    return eliminado


# ------------------------------------------------------------------ categorías

def listar_categorias():
    return producto_model.listar_categorias()


def crear_categoria(nombre):
    nombre = (nombre or "").strip() if isinstance(nombre, str) or nombre is None else ""
    if not nombre:
        raise ValidacionError("El nombre de la categoría es obligatorio")
    if len(nombre) > 60:
        raise ValidacionError("El nombre de la categoría no puede pasar de 60 caracteres")
    return producto_model.crear_categoria(nombre)