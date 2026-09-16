from db import get_connection


def obtener_todos():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre, email, telefono, creado_en "
                "FROM clientes ORDER BY id"
            )
            return cur.fetchall()
    finally:
        conn.close()


def obtener_por_id(cliente_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre, email, telefono, creado_en "
                "FROM clientes WHERE id = %s",
                (cliente_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def crear(nombre, email, telefono):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO clientes (nombre, email, telefono) "
                "VALUES (%s, %s, %s) "
                "RETURNING id, nombre, email, telefono, creado_en",
                (nombre, email, telefono),
            )
            fila = cur.fetchone()
            conn.commit()
            return fila
    finally:
        conn.close()


def actualizar(cliente_id, nombre, email, telefono):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE clientes SET nombre = %s, email = %s, telefono = %s "
                "WHERE id = %s "
                "RETURNING id, nombre, email, telefono, creado_en",
                (nombre, email, telefono, cliente_id),
            )
            fila = cur.fetchone()
            conn.commit()
            return fila
    finally:
        conn.close()


def eliminar(cliente_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM clientes WHERE id = %s RETURNING id", (cliente_id,)
            )
            fila = cur.fetchone()
            conn.commit()
            return fila
    finally:
        conn.close()
