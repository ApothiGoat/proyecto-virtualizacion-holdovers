# Gateway y Redes Docker

## Objetivo

Configurar Nginx como punto único de entrada a la aplicación El Quetzal.

El gateway será responsable de:

- Servir el frontend Vue.
- Enrutar las solicitudes hacia los microservicios.
- Utilizar descubrimiento por nombre de servicio dentro de Docker.
- Mantener la comunicación de los servicios dentro de una red Docker interna.

## Flujo de comunicación

```text
Navegador
    |
    v
localhost:8080
    |
    v
VirtualBox NAT
Host 8080 -> VM 80
    |
    v
Nginx Gateway
    |
    +-- /                  -> Vue
    +-- /api/catalogo/     -> catalogo
    +-- /api/inventario/   -> inventario
    +-- /api/clientes/     -> clientes
    +-- /api/pedidos/      -> pedidos
    +-- /api/reportes/     -> reportes