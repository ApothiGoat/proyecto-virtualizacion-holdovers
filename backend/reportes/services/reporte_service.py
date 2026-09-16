from datetime import datetime

from services import pedidos_http, clientes_http


class ValidacionError(Exception):
    pass


def _validar_periodo(desde, hasta):
    """Sin límite de 6 meses: el periodo puede abarcar cualquier rango,
    siempre que 'desde' y 'hasta' sean fechas válidas y 'desde' <= 'hasta'."""
    if not desde or not hasta:
        raise ValidacionError("Debe indicar 'desde' y 'hasta' (formato YYYY-MM-DD)")
    for nombre, valor in (("desde", desde), ("hasta", hasta)):
        try:
            datetime.strptime(valor, "%Y-%m-%d")
        except ValueError:
            raise ValidacionError(f"'{nombre}' debe tener formato YYYY-MM-DD")
    if desde > hasta:
        raise ValidacionError("'desde' no puede ser posterior a 'hasta'")
    return desde, hasta


def reporte_ventas(desde, hasta):
    """El reporte más simple: todos los pedidos del periodo, cantidad total
    de producto por pedido, y el total en Q."""
    desde, hasta = _validar_periodo(desde, hasta)
    pedidos = pedidos_http.listar_pedidos(desde=desde, hasta=hasta)

    detalle = []
    total_ventas = 0.0
    total_unidades = 0
    for pedido in pedidos:
        unidades = sum(item["cantidad"] for item in pedido["items"])
        total_unidades += unidades
        total_ventas += float(pedido["total"])
        detalle.append(
            {
                "pedido_id": pedido["id"],
                "fecha": pedido["fecha"],
                "cantidad_producto": unidades,
                "total_q": round(float(pedido["total"]), 2),
            }
        )

    return {
        "tipo": "ventas",
        "periodo": {"desde": desde, "hasta": hasta},
        "total_pedidos": len(pedidos),
        "total_unidades": total_unidades,
        "total_ventas_q": round(total_ventas, 2),
        "detalle": detalle,
    }


def reporte_clientes(desde, hasta, cliente_id=None):
    """Pedidos de todos los clientes, o de uno en específico: cantidad de
    producto, precio unitario y total, agrupado por cliente."""
    desde, hasta = _validar_periodo(desde, hasta)
    pedidos = pedidos_http.listar_pedidos(desde=desde, hasta=hasta, cliente_id=cliente_id)

    nombres_por_cliente = {}
    if cliente_id is not None:
        cliente = clientes_http.obtener_cliente(cliente_id)
        if cliente:
            nombres_por_cliente[cliente_id] = cliente["nombre"]
    else:
        for c in clientes_http.listar_clientes():
            nombres_por_cliente[c["id"]] = c["nombre"]

    grupos = {}
    for pedido in pedidos:
        cid = pedido["cliente_id"]
        clave = cid if cid is not None else "sin_cliente"
        if clave not in grupos:
            grupos[clave] = {
                "cliente_id": cid,
                "cliente_nombre": nombres_por_cliente.get(cid, "Sin cliente (mostrador)"),
                "pedidos": [],
                "total_cliente_q": 0.0,
            }

        items_detalle = [
            {
                "sku": item["sku"],
                "cantidad": item["cantidad"],
                "precio_unitario": round(float(item["precio_unitario"]), 2),
                "subtotal_q": round(item["cantidad"] * float(item["precio_unitario"]), 2),
            }
            for item in pedido["items"]
        ]
        grupos[clave]["pedidos"].append(
            {
                "pedido_id": pedido["id"],
                "fecha": pedido["fecha"],
                "items": items_detalle,
                "total_q": round(float(pedido["total"]), 2),
            }
        )
        grupos[clave]["total_cliente_q"] += float(pedido["total"])

    for grupo in grupos.values():
        grupo["total_cliente_q"] = round(grupo["total_cliente_q"], 2)

    return {
        "tipo": "clientes",
        "periodo": {"desde": desde, "hasta": hasta},
        "clientes": list(grupos.values()),
    }


def reporte_productos(desde, hasta, skus=None):
    """Pedidos asociados a uno o varios productos en el periodo, agrupados
    por SKU: unidades vendidas, ingresos, y el detalle de cada pedido."""
    desde, hasta = _validar_periodo(desde, hasta)
    pedidos = pedidos_http.listar_pedidos(desde=desde, hasta=hasta, skus=skus)

    grupos = {}
    for pedido in pedidos:
        for item in pedido["items"]:
            if skus and item["sku"] not in skus:
                continue
            sku = item["sku"]
            if sku not in grupos:
                grupos[sku] = {
                    "sku": sku,
                    "unidades_vendidas": 0,
                    "ingresos_q": 0.0,
                    "pedidos": [],
                }
            grupos[sku]["unidades_vendidas"] += item["cantidad"]
            grupos[sku]["ingresos_q"] += item["cantidad"] * float(item["precio_unitario"])
            grupos[sku]["pedidos"].append(
                {
                    "pedido_id": pedido["id"],
                    "fecha": pedido["fecha"],
                    "cantidad": item["cantidad"],
                    "precio_unitario": round(float(item["precio_unitario"]), 2),
                }
            )

    for grupo in grupos.values():
        grupo["ingresos_q"] = round(grupo["ingresos_q"], 2)

    return {
        "tipo": "productos",
        "periodo": {"desde": desde, "hasta": hasta},
        "productos": list(grupos.values()),
    }
