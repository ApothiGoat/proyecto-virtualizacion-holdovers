CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    carne_integrante VARCHAR(30) NOT NULL,
    cliente_id INTEGER,
    total NUMERIC(10, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'confirmado',
    fecha TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    sku VARCHAR(50) NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10, 2) NOT NULL
);
