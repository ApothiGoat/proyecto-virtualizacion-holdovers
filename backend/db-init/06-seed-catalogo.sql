\c catalogo_db
SET ROLE catalogo_user;

INSERT INTO productos (sku, nombre, categoria, precio) VALUES
('SKU-001', 'Laptop Lenovo ThinkPad', 'Electrónica', 4500.00),
('SKU-002', 'Mouse inalámbrico', 'Accesorios', 85.50),
('SKU-003', 'Monitor 24 pulgadas', 'Electrónica', 950.00),
('SKU-004', 'Teclado mecánico', 'Accesorios', 320.00),
('SKU-005', 'Silla ergonómica', 'Mobiliario', 1200.00)
ON CONFLICT (sku) DO NOTHING;