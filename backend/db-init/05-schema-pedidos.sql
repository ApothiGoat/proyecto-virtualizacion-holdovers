\c pedidos_db
SET ROLE pedidos_user;

CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    carne_integrante VARCHAR(30) NOT NULL,
    cliente_id INTEGER,
    total NUMERIC(10, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CONSTRAINT pedidos_estado_check
        CHECK (estado IN ('pendiente', 'completado', 'cancelado')),
    fecha TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    sku VARCHAR(50) NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10, 2) NOT NULL
);

-- Índices: aceleran el join pedidos, pedido_items y las consultas de /reportes
CREATE INDEX IF NOT EXISTS idx_pedido_items_pedido_id ON pedido_items(pedido_id);
CREATE INDEX IF NOT EXISTS idx_pedido_items_sku       ON pedido_items(sku);
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha          ON pedidos(fecha);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_id     ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado         ON pedidos(estado);