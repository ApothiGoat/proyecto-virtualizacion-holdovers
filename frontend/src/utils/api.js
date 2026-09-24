// Lee el mensaje de error de una respuesta del backend ({error, detalle?})
async function extraerError(res, porDefecto) {
  const cuerpo = await res.json().catch(() => ({}));
  const detalle =
    Array.isArray(cuerpo.detalle) && cuerpo.detalle.length && typeof cuerpo.detalle[0] === "string"
      ? `: ${cuerpo.detalle.join("; ")}`
      : "";
  return (cuerpo.error ?? porDefecto) + detalle;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

/**
 * Suma (delta > 0) o resta (delta < 0) unidades al stock de un SKU.
 * Usa los endpoints atómicos de inventario: restar nunca deja el stock por
 * debajo de 0 (el servidor responde 409 si no alcanza).
 */
export async function ajustarStock(sku, delta) {
  const cantidad = Math.trunc(Number(delta));
  if (!cantidad) return;

  const accion = cantidad > 0 ? "incrementar" : "descontar";
  const res = await fetch(`/api/inventario/stock/${accion}`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ items: [{ sku, cantidad: Math.abs(cantidad) }] }),
  });
  if (!res.ok) throw new Error(await extraerError(res, "No se pudo ajustar el stock"));
}

/** Crea la categoría (o devuelve la existente si el nombre ya estaba). */
export async function crearCategoria(nombre) {
  const res = await fetch("/api/catalogo/productos/categorias", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ nombre }),
  });
  if (!res.ok) throw new Error(await extraerError(res, "No se pudo crear la categoría"));
  return res.json(); // {id, nombre}
}

/**
 * Crea el producto en catálogo y, si trae stock inicial, lo registra en inventario.
 * Si el producto se crea pero el stock falla, NO lanza: devuelve el motivo en
 * `avisoStock`, porque el producto ya existe y reintentar daría "SKU duplicado".
 */
export async function crearProductoConStock(datos) {
  const { stock_inicial = 0, ajuste_stock, ...producto } = datos;

  const res = await fetch("/api/catalogo/productos", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(producto),
  });
  if (!res.ok) throw new Error(await extraerError(res, "No se pudo crear el producto"));

  let avisoStock = "";
  if (Number(stock_inicial) > 0) {
    try {
      await ajustarStock(producto.sku, stock_inicial);
    } catch (e) {
      avisoStock = e.message;
    }
  }
  return { avisoStock };
}