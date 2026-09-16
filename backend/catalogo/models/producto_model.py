from db import get_connection


def obtener_todos():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, sku, nombre, categoria, precio, creado_en "
                "FROM productos ORDER BY id"
            )
            return cur.fetchall()
    finally:
        conn.close()


def obtener_por_sku(sku):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, sku, nombre, categoria, precio, creado_en "
                "FROM productos WHERE sku = %s",
                (sku,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def crear(sku, nombre, categoria, precio):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO productos (sku, nombre, categoria, precio) "
                "VALUES (%s, %s, %s, %s) "
                "RETURNING id, sku, nombre, categoria, precio, creado_en",
                (sku, nombre, categoria, precio),
            )
            fila = cur.fetchone()
            conn.commit()
            return fila
    finally:
        conn.close()


def actualizar(sku, nombre, categoria, precio):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE productos SET nombre = %s, categoria = %s, precio = %s "
                "WHERE sku = %s "
                "RETURNING id, sku, nombre, categoria, precio, creado_en",
                (nombre, categoria, precio, sku),
            )
            fila = cur.fetchone()
            conn.commit()
            return fila
    finally:
        conn.close()


def eliminar(sku):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM productos WHERE sku = %s RETURNING sku", (sku,))
            fila = cur.fetchone()
            conn.commit()
            return fila
    finally:
        conn.close()
