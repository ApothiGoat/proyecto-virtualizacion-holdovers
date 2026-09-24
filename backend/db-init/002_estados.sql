BEGIN;

-- 'confirmado' era el único estado: equivale a una venta ya cerrada
UPDATE pedidos SET estado = 'completado' WHERE estado = 'confirmado';

ALTER TABLE pedidos ALTER COLUMN estado SET DEFAULT 'pendiente';

ALTER TABLE pedidos DROP CONSTRAINT IF EXISTS pedidos_estado_check;
ALTER TABLE pedidos
    ADD CONSTRAINT pedidos_estado_check
    CHECK (estado IN ('pendiente', 'completado', 'cancelado'));

CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);

COMMIT;