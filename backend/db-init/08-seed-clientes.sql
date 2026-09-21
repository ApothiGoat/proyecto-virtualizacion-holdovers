\c clientes_db
SET ROLE clientes_user;

INSERT INTO clientes (nombre, email, telefono) VALUES
('Distribuidora Central, S.A.', 'compras@distribuidoracentral.com', '22334455'),
('Comercial El Progreso', 'contacto@elprogreso.gt', '55667788'),
('Ferretería Los Andes', 'ventas@losandes.gt', '44556677')
ON CONFLICT (email) DO NOTHING;
