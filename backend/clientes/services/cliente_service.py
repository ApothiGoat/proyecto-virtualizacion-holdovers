from models import cliente_model


class ValidacionError(Exception):
    pass


def _validar(nombre, email):
    if not nombre or not nombre.strip():
        raise ValidacionError("El nombre es obligatorio")
    if not email or "@" not in email:
        raise ValidacionError("El email no es válido")


def listar_clientes():
    return cliente_model.obtener_todos()


def obtener_cliente(cliente_id):
    cliente = cliente_model.obtener_por_id(cliente_id)
    if cliente is None:
        raise KeyError(f"No existe el cliente con id {cliente_id}")
    return cliente


def crear_cliente(nombre, email, telefono):
    _validar(nombre, email)
    return cliente_model.crear(nombre, email, telefono)


def actualizar_cliente(cliente_id, nombre, email, telefono):
    _validar(nombre, email)
    cliente = cliente_model.actualizar(cliente_id, nombre, email, telefono)
    if cliente is None:
        raise KeyError(f"No existe el cliente con id {cliente_id}")
    return cliente


def eliminar_cliente(cliente_id):
    eliminado = cliente_model.eliminar(cliente_id)
    if eliminado is None:
        raise KeyError(f"No existe el cliente con id {cliente_id}")
    return eliminado
