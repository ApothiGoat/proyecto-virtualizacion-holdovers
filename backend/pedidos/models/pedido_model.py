from db import get_connection


def crear_pedido_con_items(carne_integrante, cliente_id, items, total):
    """Inserta el pedido y sus items en UNA sola transacción local (atomicidad
    dentro de la base de datos de 'pedidos'). Devuelve el pedido con sus items.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pedidos (carne_integrante, cliente_id, total, estado)
                VALUES (%s, %s, %s, 'confirmado')
                RETURNING id, carne_integrante, cliente_id, total, estado, fecha
                """,
                (carne_integrante, cliente_id, total),
            )
            pedido = cur.fetchone()

            for item in items:
                cur.execute(
                    """
                    INSERT INTO pedido_items (pedido_id, sku, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (pedido["id"], item["sku"], item["cantidad"], item["precio_unitario"]),
                )

            conn.commit()
            pedido["items"] = items
            return pedido
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def obtener_filtrados(desde=None, hasta=None, cliente_id=None, skus=None):
    """Lista pedidos con filtros opcionales, incluyendo sus items.

    - desde/hasta: fechas 'YYYY-MM-DD' (hasta es inclusivo, cubre todo ese día)
    - cliente_id: filtra pedidos de un cliente específico
    - skus: lista de SKUs — filtra pedidos que incluyan al menos uno de ellos

    Sin ningún filtro, devuelve todos los pedidos (equivalente al listado
    completo que antes daba obtener_todos()).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            condiciones = []
            params = []

            if desde:
                condiciones.append("p.fecha >= %s")
                params.append(desde)
            if hasta:
                # 'hasta' es inclusivo: cubre el día completo, no solo 00:00
                condiciones.append("p.fecha < (%s::date + interval '1 day')")
                params.append(hasta)
            if cliente_id is not None:
                condiciones.append("p.cliente_id = %s")
                params.append(cliente_id)

            join_sku = ""
            if skus:
                join_sku = "JOIN pedido_items pi_filtro ON pi_filtro.pedido_id = p.id"
                placeholders = ", ".join(["%s"] * len(skus))
                condiciones.append(f"pi_filtro.sku IN ({placeholders})")
                params.extend(skus)

            where_clause = " AND ".join(condiciones) if condiciones else "TRUE"

            cur.execute(
                f"""
                SELECT DISTINCT p.id, p.carne_integrante, p.cliente_id,
                       p.total, p.estado, p.fecha
                FROM pedidos p
                {join_sku}
                WHERE {where_clause}
                ORDER BY p.fecha DESC
                """,
                params,
            )
            pedidos = cur.fetchall()

            if not pedidos:
                return []

            ids = [p["id"] for p in pedidos]
            placeholders_ids = ", ".join(["%s"] * len(ids))
            cur.execute(
                f"SELECT pedido_id, sku, cantidad, precio_unitario "
                f"FROM pedido_items WHERE pedido_id IN ({placeholders_ids})",
                ids,
            )
            items_por_pedido = {}
            for item in cur.fetchall():
                items_por_pedido.setdefault(item["pedido_id"], []).append(item)

            for pedido in pedidos:
                pedido["items"] = items_por_pedido.get(pedido["id"], [])

            return pedidos
    finally:
        conn.close()


def obtener_por_id(pedido_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, carne_integrante, cliente_id, total, estado, fecha "
                "FROM pedidos WHERE id = %s",
                (pedido_id,),
            )
            pedido = cur.fetchone()
            if pedido is None:
                return None
            cur.execute(
                "SELECT sku, cantidad, precio_unitario FROM pedido_items "
                "WHERE pedido_id = %s",
                (pedido_id,),
            )
            pedido["items"] = cur.fetchall()
            return pedido
    finally:
        conn.close()
