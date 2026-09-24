from db import get_connection


def _guardar_items(cur, pedido_id, items):
    for item in items:
        cur.execute(
            """
            INSERT INTO pedido_items (pedido_id, sku, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s)
            """,
            (pedido_id, item["sku"], item["cantidad"], item["precio_unitario"]),
        )


def crear_pedido_con_items(carne_integrante, cliente_id, items, total):
    """Inserta el pedido y sus items en UNA sola transacción local (atomicidad
    dentro de la base de datos de 'pedidos'). El pedido nace 'pendiente'.
    Devuelve el pedido con sus items.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pedidos (carne_integrante, cliente_id, total, estado)
                VALUES (%s, %s, %s, 'pendiente')
                RETURNING id, carne_integrante, cliente_id, total, estado, fecha
                """,
                (carne_integrante, cliente_id, total),
            )
            pedido = cur.fetchone()
            _guardar_items(cur, pedido["id"], items)
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

    - desde/hasta: fechas 'YYYY-MM-DD' en hora de Guatemala (hasta es inclusivo)
    - cliente_id: filtra pedidos de un cliente específico
    - skus: lista de SKUs — filtra pedidos que incluyan al menos uno de ellos

    Sin ningún filtro, devuelve todos los pedidos.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            condiciones = []
            params = []

            # 'fecha' se guarda en UTC (timestamp sin zona); se compara el día
            # calendario de Guatemala para que "hoy" coincida con lo que ve el usuario.
            dia_local = "(p.fecha AT TIME ZONE 'UTC' AT TIME ZONE 'America/Guatemala')::date"
            if desde:
                condiciones.append(f"{dia_local} >= %s::date")
                params.append(desde)
            if hasta:
                condiciones.append(f"{dia_local} <= %s::date")
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


def cambiar_estado(pedido_id, nuevo_estado):
    """Transición atómica pendiente -> completado | cancelado.

    Devuelve el pedido actualizado, o None si no existe o ya no estaba
    pendiente (nadie más lo cerró entre tanto)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pedidos SET estado = %s "
                "WHERE id = %s AND estado = 'pendiente' RETURNING id",
                (nuevo_estado, pedido_id),
            )
            fila = cur.fetchone()
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return obtener_por_id(pedido_id) if fila else None


def reemplazar_pedido(pedido_id, cliente_id, items, total):
    """Edita cliente e ítems de un pedido PENDIENTE en una sola transacción.

    Devuelve el pedido actualizado, o None si no existe o ya no es pendiente."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pedidos SET cliente_id = %s, total = %s "
                "WHERE id = %s AND estado = 'pendiente' RETURNING id",
                (cliente_id, total, pedido_id),
            )
            if cur.fetchone() is None:
                conn.rollback()
                return None

            cur.execute("DELETE FROM pedido_items WHERE pedido_id = %s", (pedido_id,))
            _guardar_items(cur, pedido_id, items)
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return obtener_por_id(pedido_id)