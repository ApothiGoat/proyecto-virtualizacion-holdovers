#!/bin/bash

set -e

psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" <<-EOSQL

    CREATE USER catalogo_user
        WITH PASSWORD '$CATALOGO_DB_PASSWORD';

    CREATE DATABASE catalogo_db
        OWNER catalogo_user;

    REVOKE CONNECT ON DATABASE catalogo_db
        FROM PUBLIC;


    CREATE USER inventario_user
        WITH PASSWORD '$INVENTARIO_DB_PASSWORD';

    CREATE DATABASE inventario_db
        OWNER inventario_user;

    REVOKE CONNECT ON DATABASE inventario_db
        FROM PUBLIC;


    CREATE USER clientes_user
        WITH PASSWORD '$CLIENTES_DB_PASSWORD';

    CREATE DATABASE clientes_db
        OWNER clientes_user;

    REVOKE CONNECT ON DATABASE clientes_db
        FROM PUBLIC;


    CREATE USER pedidos_user
        WITH PASSWORD '$PEDIDOS_DB_PASSWORD';

    CREATE DATABASE pedidos_db
        OWNER pedidos_user;

    REVOKE CONNECT ON DATABASE pedidos_db
        FROM PUBLIC;

EOSQL