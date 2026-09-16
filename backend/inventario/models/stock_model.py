from db import get_connection


def obtener_todos():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sku, cantidad, actualizado_en FROM stock ORDER BY sku"
            )
            return cur.fetchall()
    finally:
        conn.close()


def obtener_por_sku(sku):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sku, cantidad, actualizado_en FROM stock WHERE sku = %s",
                (sku,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def upsert_stock(sku, cantidad):
    """Crea o fija la cantidad de un SKU (ajuste administrativo, no transaccional de pedidos)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stock (sku, cantidad)
                VALUES (%s, %s)
                ON CONFLICT (sku)
                DO UPDATE SET cantidad = EXCLUDED.cantidad, actualizado_en = now()
                RETURNING sku, cantidad, actualizado_en
                """,
                (sku, cantidad),
            )
            fila = cur.fetchone()
            conn.commit()
            return fila
    finally:
        conn.close()


def descontar_atomico(items):
    """Descuenta stock de varios SKUs en UNA sola transacción — todo o nada.

    items: lista de dicts {"sku": str, "cantidad": int}

    Usa SELECT ... FOR UPDATE para bloquear las filas involucradas mientras
    se valida y se descuenta, evitando condiciones de carrera si dos pedidos
    llegan casi al mismo tiempo por el mismo producto.

    Devuelve (True, None) si tuvo éxito, o (False, lista_de_errores) si algún
    producto no alcanzó — en cuyo caso NADA se descontó (rollback).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            errores = []
            # Bloquear en orden determinístico por SKU para evitar deadlocks
            # entre pedidos concurrentes que comparten productos.
            for item in sorted(items, key=lambda i: i["sku"]):
                cur.execute(
                    "SELECT cantidad FROM stock WHERE sku = %s FOR UPDATE",
                    (item["sku"],),
                )
                fila = cur.fetchone()
                if fila is None:
                    errores.append(f"SKU '{item['sku']}' no existe en inventario")
                elif fila["cantidad"] < item["cantidad"]:
                    errores.append(
                        f"Stock insuficiente para '{item['sku']}': "
                        f"disponible {fila['cantidad']}, solicitado {item['cantidad']}"
                    )

            if errores:
                conn.rollback()
                return False, errores

            for item in items:
                cur.execute(
                    "UPDATE stock SET cantidad = cantidad - %s, actualizado_en = now() "
                    "WHERE sku = %s",
                    (item["cantidad"], item["sku"]),
                )

            conn.commit()
            return True, None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def incrementar_atomico(items):
    """Compensación (saga): repone stock si un paso posterior (crear el pedido
    en el microservicio 'pedidos') falla DESPUÉS de haber descontado aquí.

    Es el mecanismo que sustituye a una transacción distribuida real entre
    bases de datos separadas — se documenta como decisión de arquitectura.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for item in items:
                cur.execute(
                    "UPDATE stock SET cantidad = cantidad + %s, actualizado_en = now() "
                    "WHERE sku = %s",
                    (item["cantidad"], item["sku"]),
                )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
