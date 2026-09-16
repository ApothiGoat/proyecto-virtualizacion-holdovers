\c inventario_db
SET ROLE inventario_user;
CREATE TABLE IF NOT EXISTS stock (
    sku VARCHAR(50) PRIMARY KEY,
    cantidad INTEGER NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
    actualizado_en TIMESTAMP NOT NULL DEFAULT now()
);
