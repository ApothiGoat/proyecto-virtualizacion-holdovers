import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import reporte_service
from services.reporte_service import ValidacionError


PEDIDO_EJEMPLO_1 = {
    "id": 1,
    "cliente_id": 10,
    "total": 150.0,
    "fecha": "2026-03-05T10:00:00",
    "items": [
        {"sku": "SKU-A", "cantidad": 2, "precio_unitario": 50.0},
        {"sku": "SKU-B", "cantidad": 1, "precio_unitario": 50.0},
    ],
}

PEDIDO_EJEMPLO_2 = {
    "id": 2,
    "cliente_id": None,
    "total": 30.0,
    "fecha": "2026-03-10T12:00:00",
    "items": [{"sku": "SKU-A", "cantidad": 3, "precio_unitario": 10.0}],
}


def test_rechaza_periodo_sin_fechas():
    with pytest.raises(ValidacionError, match="desde"):
        reporte_service.reporte_ventas(None, "2026-03-31")


def test_rechaza_formato_de_fecha_invalido():
    with pytest.raises(ValidacionError, match="YYYY-MM-DD"):
        reporte_service.reporte_ventas("05-03-2026", "2026-03-31")


def test_rechaza_desde_mayor_a_hasta():
    with pytest.raises(ValidacionError, match="posterior"):
        reporte_service.reporte_ventas("2026-06-01", "2026-01-01")


def test_acepta_periodo_mayor_a_seis_meses(mocker):
    """Requisito explícito: NO hay límite de 6 meses en reportes."""
    mocker.patch("services.reporte_service.pedidos_http.listar_pedidos", return_value=[])
    resultado = reporte_service.reporte_ventas("2020-01-01", "2026-12-31")
    assert resultado["periodo"]["desde"] == "2020-01-01"
    assert resultado["periodo"]["hasta"] == "2026-12-31"


def test_reporte_ventas_totaliza_correctamente(mocker):
    mocker.patch(
        "services.reporte_service.pedidos_http.listar_pedidos",
        return_value=[PEDIDO_EJEMPLO_1, PEDIDO_EJEMPLO_2],
    )
    resultado = reporte_service.reporte_ventas("2026-03-01", "2026-03-31")
    assert resultado["total_pedidos"] == 2
    assert resultado["total_unidades"] == 6  # 2+1 del pedido1, 3 del pedido2
    assert resultado["total_ventas_q"] == 180.0  # 150 + 30
    assert resultado["detalle"][0]["cantidad_producto"] == 3


def test_reporte_clientes_agrupa_por_cliente(mocker):
    mocker.patch(
        "services.reporte_service.pedidos_http.listar_pedidos",
        return_value=[PEDIDO_EJEMPLO_1],
    )
    mocker.patch(
        "services.reporte_service.clientes_http.listar_clientes",
        return_value=[{"id": 10, "nombre": "Ferretería z.12"}],
    )
    resultado = reporte_service.reporte_clientes("2026-03-01", "2026-03-31")
    assert len(resultado["clientes"]) == 1
    grupo = resultado["clientes"][0]
    assert grupo["cliente_nombre"] == "Ferretería z.12"
    assert grupo["total_cliente_q"] == 150.0
    assert grupo["pedidos"][0]["items"][0]["subtotal_q"] == 100.0  # 2 * 50


def test_reporte_clientes_pedido_sin_cliente_no_revienta(mocker):
    mocker.patch(
        "services.reporte_service.pedidos_http.listar_pedidos",
        return_value=[PEDIDO_EJEMPLO_2],
    )
    mocker.patch("services.reporte_service.clientes_http.listar_clientes", return_value=[])
    resultado = reporte_service.reporte_clientes("2026-03-01", "2026-03-31")
    assert resultado["clientes"][0]["cliente_nombre"] == "Sin cliente (mostrador)"


def test_reporte_productos_agrupa_por_sku(mocker):
    mocker.patch(
        "services.reporte_service.pedidos_http.listar_pedidos",
        return_value=[PEDIDO_EJEMPLO_1, PEDIDO_EJEMPLO_2],
    )
    resultado = reporte_service.reporte_productos("2026-03-01", "2026-03-31")
    productos = {p["sku"]: p for p in resultado["productos"]}
    assert productos["SKU-A"]["unidades_vendidas"] == 5  # 2 + 3
    assert productos["SKU-A"]["ingresos_q"] == 130.0  # 2*50 + 3*10
    assert productos["SKU-B"]["unidades_vendidas"] == 1


def test_reporte_productos_filtra_por_sku_especifico(mocker):
    mocker.patch(
        "services.reporte_service.pedidos_http.listar_pedidos",
        return_value=[PEDIDO_EJEMPLO_1],
    )
    resultado = reporte_service.reporte_productos("2026-03-01", "2026-03-31", skus=["SKU-B"])
    assert len(resultado["productos"]) == 1
    assert resultado["productos"][0]["sku"] == "SKU-B"
