CREATE USER catalogo_user WITH PASSWORD 'catalogo_pass';
CREATE DATABASE catalogo_db OWNER catalogo_user;

CREATE USER inventario_user WITH PASSWORD 'inventario_pass';
CREATE DATABASE inventario_db OWNER inventario_user;

CREATE USER clientes_user WITH PASSWORD 'clientes_pass';
CREATE DATABASE clientes_db OWNER clientes_user;

CREATE USER pedidos_user WITH PASSWORD 'pedidos_pass';
CREATE DATABASE pedidos_db OWNER pedidos_user;
