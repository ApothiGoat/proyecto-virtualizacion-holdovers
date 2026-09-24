\c catalogo_db
SET ROLE catalogo_user;

CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL
);

-- Sin duplicados aunque cambie mayúsculas/minúsculas ("Electrónica" = "electrónica")
CREATE UNIQUE INDEX IF NOT EXISTS idx_categorias_nombre_lower ON categorias (lower(nombre));

-- Respaldo: las categorías que ya usan los productos existentes
INSERT INTO categorias (nombre)
SELECT DISTINCT trim(categoria) FROM productos
WHERE categoria IS NOT NULL AND trim(categoria) <> ''
ON CONFLICT DO NOTHING;