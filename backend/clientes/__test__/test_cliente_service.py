import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import cliente_service
from services.cliente_service import ValidacionError


def test_crear_cliente_rechaza_nombre_vacio():
    with pytest.raises(ValidacionError, match="nombre"):
        cliente_service.crear_cliente(nombre="", email="a@b.com", telefono="123")


def test_crear_cliente_rechaza_email_invalido():
    with pytest.raises(ValidacionError, match="email"):
        cliente_service.crear_cliente(nombre="Ana", email="no-es-un-email", telefono="123")


def test_crear_cliente_exitoso(mocker):
    crear_mock = mocker.patch(
        "services.cliente_service.cliente_model.crear",
        return_value={"id": 1, "nombre": "Ana", "email": "ana@correo.com"},
    )
    resultado = cliente_service.crear_cliente(nombre="Ana", email="ana@correo.com", telefono="123")
    crear_mock.assert_called_once()
    assert resultado["id"] == 1


def test_obtener_cliente_inexistente(mocker):
    mocker.patch("services.cliente_service.cliente_model.obtener_por_id", return_value=None)
    with pytest.raises(KeyError):
        cliente_service.obtener_cliente(999)
