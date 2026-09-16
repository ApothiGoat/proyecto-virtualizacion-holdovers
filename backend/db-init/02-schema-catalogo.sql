\c catalogo_db
SET ROLE catalogo_user;
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    categoria VARCHAR(80),
    precio NUMERIC(10, 2) NOT NULL CHECK (precio > 0),
    creado_en TIMESTAMP NOT NULL DEFAULT now()
);
