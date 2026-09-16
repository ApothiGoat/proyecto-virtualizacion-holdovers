"""Pruebas unitarias del servicio de catalogo — el modelo (acceso a BD) se
mockea, así que estas pruebas corren rápido y sin necesitar Postgres."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import producto_service
from services.producto_service import ValidacionError


def test_crear_producto_rechaza_sku_vacio(mocker):
    with pytest.raises(ValidacionError, match="SKU"):
        producto_service.crear_producto(sku="", nombre="Martillo", categoria="Herramientas", precio=50)


def test_crear_producto_rechaza_precio_negativo(mocker):
    with pytest.raises(ValidacionError, match="precio"):
        producto_service.crear_producto(sku="SKU-1", nombre="Martillo", categoria="Herramientas", precio=-10)


def test_crear_producto_rechaza_precio_cero(mocker):
    with pytest.raises(ValidacionError, match="precio"):
        producto_service.crear_producto(sku="SKU-1", nombre="Martillo", categoria="Herramientas", precio=0)


def test_crear_producto_rechaza_sku_duplicado(mocker):
    mocker.patch(
        "services.producto_service.producto_model.obtener_por_sku",
        return_value={"sku": "SKU-1"},
    )
    with pytest.raises(ValidacionError, match="Ya existe"):
        producto_service.crear_producto(sku="SKU-1", nombre="Martillo", categoria="Herramientas", precio=50)


def test_crear_producto_exitoso_llama_al_modelo(mocker):
    mocker.patch(
        "services.producto_service.producto_model.obtener_por_sku",
        return_value=None,
    )
    crear_mock = mocker.patch(
        "services.producto_service.producto_model.crear",
        return_value={"sku": "SKU-1", "nombre": "Martillo", "categoria": "Herramientas", "precio": 50},
    )
    resultado = producto_service.crear_producto(
        sku="SKU-1", nombre="Martillo", categoria="Herramientas", precio=50
    )
    crear_mock.assert_called_once_with("SKU-1", "Martillo", "Herramientas", 50)
    assert resultado["sku"] == "SKU-1"


def test_obtener_producto_inexistente_lanza_keyerror(mocker):
    mocker.patch(
        "services.producto_service.producto_model.obtener_por_sku",
        return_value=None,
    )
    with pytest.raises(KeyError):
        producto_service.obtener_producto("NO-EXISTE")
