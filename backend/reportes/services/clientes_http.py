"""Cliente HTTP hacia el microservicio 'clientes'."""
import os
import requests

CLIENTES_URL = os.environ.get("CLIENTES_URL", "http://clientes:5000")
TIMEOUT = 10


def obtener_cliente(cliente_id):
    resp = requests.get(f"{CLIENTES_URL}/clientes/{cliente_id}", timeout=TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def listar_clientes():
    resp = requests.get(f"{CLIENTES_URL}/clientes", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()
