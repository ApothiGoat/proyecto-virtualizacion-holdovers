\c inventario_db
SET ROLE inventario_user;

INSERT INTO stock (sku, cantidad) VALUES
('SKU-001', 15),
('SKU-002', 50),
('SKU-003', 20),
('SKU-004', 30),
('SKU-005', 8)
ON CONFLICT (sku) DO NOTHING;