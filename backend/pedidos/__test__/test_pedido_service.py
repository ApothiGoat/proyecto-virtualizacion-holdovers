"""Pruebas unitarias de pedidos — validan el flujo completo de negocio
(precio real desde catalogo, descuento atómico en inventario, y la
compensación/saga si falla el guardado del pedido) usando mocks para las
llamadas HTTP y de base de datos."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import pedido_service
from services.pedido_service import ValidacionError, ProductoNoEncontradoError
from services.clientes_http import StockInsuficienteError


def test_crear_pedido_rechaza_sin_carne(mocker):
    with pytest.raises(ValidacionError, match="carné"):
        pedido_service.crear_pedido(
            carne_integrante="", cliente_id=None, items=[{"sku": "SKU-1", "cantidad": 1}]
        )


def test_crear_pedido_rechaza_sin_items(mocker):
    with pytest.raises(ValidacionError, match="al menos un item"):
        pedido_service.crear_pedido(carne_integrante="12345", cliente_id=None, items=[])


def test_crear_pedido_rechaza_producto_inexistente(mocker):
    mocker.patch("services.pedido_service.clientes_http.obtener_producto", return_value=None)
    with pytest.raises(ProductoNoEncontradoError):
        pedido_service.crear_pedido(
            carne_integrante="12345", cliente_id=None, items=[{"sku": "NO-EXISTE", "cantidad": 1}]
        )


def test_crear_pedido_usa_precio_del_catalogo_no_del_cliente(mocker):
    """El precio SIEMPRE viene de catalogo, aunque el request traiga otro valor
    (evita que alguien manipule el precio desde el frontend)."""
    mocker.patch(
        "services.pedido_service.clientes_http.obtener_producto",
        return_value={"sku": "SKU-1", "precio": 99.99},
    )
    mocker.patch("services.pedido_service.clientes_http.descontar_stock")
    crear_mock = mocker.patch(
        "services.pedido_service.pedido_model.crear_pedido_con_items",
        return_value={"id": 1, "items": []},
    )
    pedido_service.crear_pedido(
        carne_integrante="12345", cliente_id=None, items=[{"sku": "SKU-1", "cantidad": 2}]
    )
    args, _ = crear_mock.call_args
    items_guardados = args[2]
    assert items_guardados[0]["precio_unitario"] == 99.99
    assert args[3] == pytest.approx(199.98)


def test_crear_pedido_propaga_stock_insuficiente(mocker):
    mocker.patch(
        "services.pedido_service.clientes_http.obtener_producto",
        return_value={"sku": "SKU-1", "precio": 10},
    )
    mocker.patch(
        "services.pedido_service.clientes_http.descontar_stock",
        side_effect=StockInsuficienteError(["Stock insuficiente para 'SKU-1'"]),
    )
    with pytest.raises(StockInsuficienteError):
        pedido_service.crear_pedido(
            carne_integrante="12345", cliente_id=None, items=[{"sku": "SKU-1", "cantidad": 100}]
        )


def test_crear_pedido_compensa_stock_si_falla_el_guardado(mocker):
    """Caso clave de la saga: el stock YA se descontó en inventario, pero
    guardar el pedido en la BD de pedidos falla. Se debe reponer el stock."""
    mocker.patch(
        "services.pedido_service.clientes_http.obtener_producto",
        return_value={"sku": "SKU-1", "precio": 10},
    )
    mocker.patch("services.pedido_service.clientes_http.descontar_stock")
    incrementar_mock = mocker.patch("services.pedido_service.clientes_http.incrementar_stock")
    mocker.patch(
        "services.pedido_service.pedido_model.crear_pedido_con_items",
        side_effect=Exception("la base de datos de pedidos se cayó"),
    )

    with pytest.raises(Exception, match="se cayó"):
        pedido_service.crear_pedido(
            carne_integrante="12345", cliente_id=None, items=[{"sku": "SKU-1", "cantidad": 2}]
        )

    incrementar_mock.assert_called_once_with([{"sku": "SKU-1", "cantidad": 2}])
