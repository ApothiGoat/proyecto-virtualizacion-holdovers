\c pedidos_db
SET ROLE pedidos_user;

-- Pedido 1: con cliente asociado (cliente_id = 1, "Distribuidora Central, S.A.")
WITH nuevo_pedido AS (
    INSERT INTO pedidos (carne_integrante, cliente_id, total, estado)
    VALUES ('1186023', 1, 9256.50, 'confirmado')
    RETURNING id
)
INSERT INTO pedido_items (pedido_id, sku, cantidad, precio_unitario)
SELECT id, 'SKU-001', 2, 4500.00 FROM nuevo_pedido
UNION ALL
SELECT id, 'SKU-002', 3, 85.50 FROM nuevo_pedido;

-- Pedido 2: sin cliente asociado (cliente_id NULL), prueba de que es opcional
WITH nuevo_pedido AS (
    INSERT INTO pedidos (carne_integrante, cliente_id, total, estado)
    VALUES ('1186023', NULL, 950.00, 'confirmado')
    RETURNING id
)
INSERT INTO pedido_items (pedido_id, sku, cantidad, precio_unitario)
SELECT id, 'SKU-003', 1, 950.00 FROM nuevo_pedido;