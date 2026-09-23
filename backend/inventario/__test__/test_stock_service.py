"""Pruebas unitarias de inventario — foco en la regla de negocio más
importante del proyecto: el descuento atómico de stock."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import stock_service
from services.stock_service import ValidacionError, StockInsuficienteError


def test_descontar_rechaza_lista_vacia(mocker):
    with pytest.raises(ValidacionError, match="lista"):
        stock_service.descontar_stock([])


def test_descontar_rechaza_cantidad_negativa(mocker):
    with pytest.raises(ValidacionError, match="mayor a 0"):
        stock_service.descontar_stock([{"sku": "SKU-1", "cantidad": -5}])


def test_descontar_propaga_error_si_stock_insuficiente(mocker):
    mocker.patch(
        "services.stock_service.stock_model.descontar_atomico",
        return_value=(False, ["Stock insuficiente para 'SKU-1'"]),
    )
    with pytest.raises(StockInsuficienteError):
        stock_service.descontar_stock([{"sku": "SKU-1", "cantidad": 100}])


def test_descontar_exitoso_no_lanza_excepcion(mocker):
    mock_descuento = mocker.patch(
        "services.stock_service.stock_model.descontar_atomico",
        return_value=(True, None),
    )
    stock_service.descontar_stock([{"sku": "SKU-1", "cantidad": 2}])
    mock_descuento.assert_called_once()


def test_descontar_todo_o_nada_no_llama_incrementar_por_si_solo(mocker):
    """El 'todo o nada' vive en el modelo (una sola transacción SQL);
    aquí verificamos que el servicio no intente compensar manualmente
    cuando el propio descuento ya fue atómico."""
    incrementar_mock = mocker.patch("services.stock_service.stock_model.incrementar_atomico")
    mocker.patch(
        "services.stock_service.stock_model.descontar_atomico",
        return_value=(False, ["insuficiente"]),
    )
    with pytest.raises(StockInsuficienteError):
        stock_service.descontar_stock([{"sku": "SKU-1", "cantidad": 5}])
    incrementar_mock.assert_not_called()
