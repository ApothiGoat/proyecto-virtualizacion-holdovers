<script setup>
import { computed, onMounted, ref } from "vue";
import ProductoModal from "../components/ProductoModal.vue";
import { ajustarStock, crearCategoria, crearProductoConStock } from "../utils/api.js";

const productos = ref([]); // [{sku, nombre, categoria, precio}]
const stockPorSku = ref({}); // {sku: cantidad}
const busqueda = ref("");
const cargando = ref(true);

const modalAbierto = ref(false);
const productoEnEdicion = ref(null); // null = creando
const categorias = ref([]); // nombres de categorías (vienen del catálogo)
const errorProducto = ref(""); // error mostrado dentro del modal
const aviso = ref(""); // avisos/errores de la vista (eliminar, stock inicial)

const UMBRAL_STOCK_BAJO = 10;

async function leerError(res, porDefecto) {
  const cuerpo = await res.json().catch(() => ({}));
  return cuerpo.error ?? porDefecto;
}

async function cargar() {
  cargando.value = true;
  try {
    const [productosRes, stockRes, categoriasRes] = await Promise.all([
      fetch("/api/catalogo/productos").then((r) => r.json()),
      fetch("/api/inventario/stock").then((r) => r.json()),
      // tolerante: si el endpoint falla, se usan las categorías de los productos
      fetch("/api/catalogo/productos/categorias")
        .then((r) => (r.ok ? r.json() : []))
        .catch(() => []),
    ]);
    productos.value = productosRes;
    stockPorSku.value = Object.fromEntries(stockRes.map((s) => [s.sku, s.cantidad]));

    const nombres = Array.isArray(categoriasRes) ? categoriasRes.map((c) => c.nombre) : [];
    categorias.value = [...new Set([...nombres, ...productosRes.map((p) => p.categoria)])]
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b));
  } catch (e) {
    console.error("No se pudo cargar el inventario", e);
  } finally {
    cargando.value = false;
  }
}

const productosFiltrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase();
  if (!q) return productos.value;
  return productos.value.filter(
    (p) => p.nombre.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)
  );
});

function stockDe(sku) {
  return stockPorSku.value[sku] ?? 0;
}

// Stock del producto que se está editando (se actualiza solo tras cada recarga)
const stockActualEdicion = computed(() =>
  productoEnEdicion.value ? stockDe(productoEnEdicion.value.sku) : 0
);

function abrirCreacion() {
  errorProducto.value = "";
  productoEnEdicion.value = null;
  modalAbierto.value = true;
}

function abrirEdicion(producto) {
  errorProducto.value = "";
  productoEnEdicion.value = producto;
  modalAbierto.value = true;
}

async function agregarCategoria(nombre) {
  errorProducto.value = "";
  try {
    const categoria = await crearCategoria(nombre);
    if (!categorias.value.includes(categoria.nombre)) {
      categorias.value = [...categorias.value, categoria.nombre].sort((a, b) =>
        a.localeCompare(b)
      );
    }
  } catch (e) {
    errorProducto.value = e.message;
  }
}

// Edición: primero los datos del producto (idempotente), luego el ajuste de stock.
// Así, si el stock falla, reintentar no duplica nada: el PUT se repite igual
// y el ajuste solo se aplica cuando el servidor lo acepta.
async function actualizarProducto(datos) {
  const { ajuste_stock = 0, stock_inicial, ...producto } = datos;

  const res = await fetch(`/api/catalogo/productos/${encodeURIComponent(producto.sku)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(producto),
  });
  if (!res.ok) throw new Error(await leerError(res, "Error al guardar el producto"));

  if (ajuste_stock) {
    try {
      await ajustarStock(producto.sku, ajuste_stock);
    } catch (e) {
      throw new Error(`Los datos del producto se guardaron, pero el stock no se ajustó: ${e.message}`);
    }
  }
}

async function guardarProducto(datos) {
  errorProducto.value = "";
  aviso.value = "";
  const esEdicion = !!productoEnEdicion.value;

  try {
    if (esEdicion) {
      await actualizarProducto(datos);
    } else {
      const { avisoStock } = await crearProductoConStock(datos);
      if (avisoStock) {
        aviso.value = `El producto se creó, pero no se pudo registrar el stock inicial (${avisoStock}). Ajústalo editando el producto.`;
      }
    }
    modalAbierto.value = false;
    await cargar();
  } catch (e) {
    errorProducto.value = e.message;
    // Refresca tabla y stock actual: puede haber cambiado (otro usuario, o el PUT ya se guardó)
    if (esEdicion) await cargar();
  }
}

async function eliminarProducto(sku) {
  if (!confirm(`¿Eliminar el producto ${sku}? Esta acción no se puede deshacer.`)) return;
  aviso.value = "";
  try {
    const res = await fetch(`/api/catalogo/productos/${encodeURIComponent(sku)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(await leerError(res, "Error al eliminar el producto"));
    await cargar();
  } catch (e) {
    aviso.value = e.message;
  }
}

onMounted(cargar);
</script>

<template>
  <div class="inventario">
    <p v-if="aviso" class="alert-error" role="alert">{{ aviso }}</p>

    <div class="toolbar">
      <input
        v-model="busqueda"
        class="search"
        type="search"
        placeholder="Buscar por SKU o nombre"
        aria-label="Buscar productos"
      />
      <button class="btn btn-primary" @click="abrirCreacion">+ Nuevo producto</button>
    </div>

    <div class="card table-card">
      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Precio</th>
            <th>Stock</th>
            <th>Estado</th>
            <th aria-label="Acciones"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in productosFiltrados" :key="p.sku">
            <td>{{ p.sku }}</td>
            <td>{{ p.nombre }}</td>
            <td>{{ p.categoria }}</td>
            <td>Q {{ Number(p.precio).toFixed(2) }}</td>
            <td>{{ stockDe(p.sku) }}</td>
            <td>
              <span
                class="badge"
                :class="stockDe(p.sku) < UMBRAL_STOCK_BAJO ? 'badge-danger' : 'badge-ok'"
              >
                {{ stockDe(p.sku) < UMBRAL_STOCK_BAJO ? "Stock bajo" : "Disponible" }}
              </span>
            </td>
            <td class="actions">
              <button class="btn-icon" aria-label="Editar producto" @click="abrirEdicion(p)">✎</button>
              <button class="btn-icon" aria-label="Eliminar producto" @click="eliminarProducto(p.sku)">🗑</button>
            </td>
          </tr>
          <tr v-if="!cargando && productosFiltrados.length === 0">
            <td colspan="7" class="empty">No hay productos que coincidan con la búsqueda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ProductoModal
      :open="modalAbierto"
      :producto="productoEnEdicion"
      :categorias="categorias"
      :stock-actual="stockActualEdicion"
      :error="errorProducto"
      @close="modalAbierto = false"
      @save="guardarProducto"
      @nueva-categoria="agregarCategoria"
    />
  </div>
</template>

<style scoped>
.inventario {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.search {
  width: 320px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  color: var(--text);
  font-size: 14px;
}

.table-card {
  padding: 8px 0;
  overflow-x: auto;
}

.actions {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}

.empty {
  text-align: center;
  color: var(--text-faint);
  padding: 32px 16px;
}
</style>