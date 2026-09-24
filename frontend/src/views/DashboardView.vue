<script setup>
import { computed, onMounted, ref } from "vue";
import ProductoModal from "../components/ProductoModal.vue";
import PedidoFormModal from "../components/PedidoFormModal.vue";
import { crearCategoria, crearProductoConStock } from "../utils/api.js";

const cargando = ref(true);

const productos = ref([]); // se reutiliza para el form de pedido
const clientes = ref([]);
const categorias = ref([]); // nombres

const modalProductoAbierto = ref(false);
const modalPedidoAbierto = ref(false);
const errorProducto = ref("");
const errorPedido = ref("");
const avisoDashboard = ref("");

const kpis = ref({
  totalProductos: 0,
  valorInventario: 0,
  pedidosHoy: 0,
  stockBajoCount: 0,
});

const stockBajo = ref([]); // [{sku, nombre, stock}]
const ventasPorProducto = ref([]); // [{sku, nombre, unidades, ingresos}]

// Fecha local (no UTC) en formato YYYY-MM-DD
function isoLocal(d) {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${dia}`;
}
function hoyISO() {
  return isoLocal(new Date());
}
function hace7diasISO() {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return isoLocal(d);
}

async function cargarDashboard() {
  cargando.value = true;
  try {
    const [productosRes, stockRes, pedidosHoyRes, ventasRes, categoriasRes] = await Promise.all([
      fetch("/api/catalogo/productos").then((r) => r.json()),
      fetch("/api/inventario/stock").then((r) => r.json()),
      fetch(`/api/pedidos?desde=${hoyISO()}&hasta=${hoyISO()}`).then((r) => r.json()),
      fetch(`/api/reportes/productos?desde=${hace7diasISO()}&hasta=${hoyISO()}`).then((r) => r.json()),
      // tolerante: si el endpoint falla, se usan las categorías de los productos
      fetch("/api/catalogo/productos/categorias")
        .then((r) => (r.ok ? r.json() : []))
        .catch(() => []),
    ]);

    const umbralStockBajo = 10;
    const stockPorSku = Object.fromEntries(stockRes.map((s) => [s.sku, s.cantidad]));
    const nombrePorSku = Object.fromEntries(productosRes.map((p) => [p.sku, p.nombre]));

    productos.value = productosRes;

    const nombresCategorias = Array.isArray(categoriasRes) ? categoriasRes.map((c) => c.nombre) : [];
    categorias.value = [...new Set([...nombresCategorias, ...productosRes.map((p) => p.categoria)])]
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b));

    kpis.value.totalProductos = productosRes.length;
    kpis.value.valorInventario = productosRes.reduce(
      (acc, p) => acc + p.precio * (stockPorSku[p.sku] ?? 0),
      0
    );
    kpis.value.pedidosHoy = Array.isArray(pedidosHoyRes)
      ? pedidosHoyRes.filter((p) => p.estado !== "cancelado").length
      : 0;

    stockBajo.value = productosRes
      .map((p) => ({ sku: p.sku, nombre: p.nombre, stock: stockPorSku[p.sku] ?? 0 }))
      .filter((p) => p.stock < umbralStockBajo)
      .sort((a, b) => a.stock - b.stock);

    kpis.value.stockBajoCount = stockBajo.value.length;

    // /reportes/productos devuelve {productos: [{sku, unidades_vendidas, ingresos_q, pedidos}]}
    // (sin nombre), por eso se mapea acá y el nombre se resuelve con el catálogo.
    const filas = Array.isArray(ventasRes?.productos)
      ? ventasRes.productos
      : Array.isArray(ventasRes)
        ? ventasRes
        : [];
    ventasPorProducto.value = filas
      .map((v) => ({
        sku: v.sku,
        nombre: nombrePorSku[v.sku] ?? v.sku,
        unidades: v.unidades_vendidas ?? v.unidades ?? 0,
        ingresos: Number(v.ingresos_q ?? v.ingresos ?? 0),
      }))
      .sort((a, b) => b.ingresos - a.ingresos)
      .slice(0, 6);
  } catch (e) {
    // TODO: mostrar estado de error en la UI (toast / banner)
    console.error("No se pudo cargar el dashboard", e);
  } finally {
    cargando.value = false;
  }
}

const maxIngresos = computed(() =>
  Math.max(1, ...ventasPorProducto.value.map((v) => v.ingresos ?? 0))
);

function formatQ(valor) {
  return `Q ${Number(valor ?? 0).toLocaleString("es-GT", { minimumFractionDigits: 2 })}`;
}

function abrirNuevoProducto() {
  errorProducto.value = "";
  modalProductoAbierto.value = true;
}

async function agregarCategoria(nombre) {
  errorProducto.value = "";
  try {
    const categoria = await crearCategoria(nombre);
    if (!categorias.value.includes(categoria.nombre)) {
      categorias.value = [...categorias.value, categoria.nombre].sort((a, b) => a.localeCompare(b));
    }
  } catch (e) {
    errorProducto.value = e.message;
  }
}

async function guardarProducto(datos) {
  errorProducto.value = "";
  try {
    const { avisoStock } = await crearProductoConStock(datos);
    modalProductoAbierto.value = false;
    avisoDashboard.value = avisoStock
      ? `El producto se creó, pero no se pudo registrar el stock inicial (${avisoStock}). Ajústalo desde Inventario.`
      : "";
    await cargarDashboard();
  } catch (e) {
    errorProducto.value = e.message;
  }
}

async function abrirNuevoPedido() {
  errorPedido.value = "";
  try {
    clientes.value = await fetch("/api/clientes").then((r) => r.json());
    modalPedidoAbierto.value = true;
  } catch (e) {
    console.error("No se pudieron cargar los clientes", e);
  }
}

async function guardarPedido(datos) {
  errorPedido.value = "";
  try {
    const res = await fetch("/api/pedidos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });
    const cuerpo = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(cuerpo.error ?? "Error al generar el pedido");
    modalPedidoAbierto.value = false;
    await cargarDashboard();
  } catch (e) {
    errorPedido.value = e.message;
  }
}

onMounted(cargarDashboard);
</script>

<template>
  <div class="dashboard">
    <p v-if="avisoDashboard" class="alert-error" role="alert">{{ avisoDashboard }}</p>

    <section class="kpis">
      <div class="card kpi">
        <div class="kpi-label">Total de productos</div>
        <div class="kpi-value">{{ kpis.totalProductos }}</div>
      </div>
      <div class="card kpi">
        <div class="kpi-label">Valor del inventario</div>
        <div class="kpi-value">{{ formatQ(kpis.valorInventario) }}</div>
      </div>
      <div class="card kpi">
        <div class="kpi-label">Pedidos de hoy</div>
        <div class="kpi-value">{{ kpis.pedidosHoy }}</div>
      </div>
      <div class="card kpi kpi-alert" :class="{ active: kpis.stockBajoCount > 0 }">
        <div class="kpi-label">Alerta de stock bajo</div>
        <div class="kpi-value">{{ kpis.stockBajoCount }}</div>
      </div>
    </section>

    <section class="grid-2">
      <div class="left-col">
        <div class="card panel">
          <h2>Ventas por producto <span class="panel-sub">últimos 7 días</span></h2>
          <div class="bars">
            <div v-for="v in ventasPorProducto" :key="v.sku" class="bar-row">
              <div class="bar-label" :title="v.nombre">{{ v.nombre }}</div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: ((v.ingresos ?? 0) / maxIngresos) * 100 + '%' }"
                />
              </div>
              <div class="bar-value">{{ formatQ(v.ingresos) }}</div>
            </div>
            <p v-if="!cargando && ventasPorProducto.length === 0" class="empty">
              Todavía no hay ventas registradas en el periodo.
            </p>
          </div>
        </div>

        <div class="quick-actions">
          <button class="card quick-action" @click="abrirNuevoProducto">
            <span class="quick-action-icon">+</span>
            <div>
              <div class="quick-action-title">Nuevo producto</div>
              <div class="quick-action-sub">Agregar al catálogo</div>
            </div>
          </button>

          <button class="card quick-action" @click="abrirNuevoPedido">
            <span class="quick-action-icon">+</span>
            <div>
              <div class="quick-action-title">Nuevo pedido</div>
              <div class="quick-action-sub">Registrar una venta</div>
            </div>
          </button>
        </div>
      </div>

      <div class="card panel">
        <h2>Stock bajo</h2>
        <ul class="stock-list">
          <li v-for="p in stockBajo" :key="p.sku">
            <span>{{ p.nombre }}</span>
            <span class="badge badge-danger">{{ p.stock }} und.</span>
          </li>
          <li v-if="!cargando && stockBajo.length === 0" class="empty">
            Todo el inventario está en niveles saludables.
          </li>
        </ul>
      </div>
    </section>

    <ProductoModal
      :open="modalProductoAbierto"
      :producto="null"
      :categorias="categorias"
      :error="errorProducto"
      @close="modalProductoAbierto = false"
      @save="guardarProducto"
      @nueva-categoria="agregarCategoria"
    />

    <PedidoFormModal
      :open="modalPedidoAbierto"
      :pedido="null"
      :productos="productos"
      :clientes="clientes"
      :error="errorPedido"
      @close="modalPedidoAbierto = false"
      @save="guardarPedido"
    />
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi {
  padding: 20px;
}

.kpi-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 10px;
}

.kpi-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
}

.kpi-alert.active .kpi-value {
  color: var(--warning);
}

.grid-2 {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  align-items: start;
}

.left-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  text-align: left;
  border: 1px solid var(--border-soft);
  color: var(--text);
  transition: border-color 0.15s ease, transform 0.12s ease;
}

.quick-action:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.quick-action-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--accent-gradient);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.quick-action-title {
  font-size: 14px;
  font-weight: 600;
}

.quick-action-sub {
  font-size: 12px;
  color: var(--text-faint);
  margin-top: 2px;
}

.panel {
  padding: 22px;
}

.panel h2 {
  font-size: 16px;
  margin-bottom: 18px;
}

.panel-sub {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 400;
  color: var(--text-faint);
  margin-left: 8px;
}

.bars {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bar-row {
  display: grid;
  grid-template-columns: 120px 1fr 90px;
  align-items: center;
  gap: 12px;
}

.bar-label {
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-track {
  height: 8px;
  background: var(--bg-elevated);
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--accent-gradient);
  border-radius: 999px;
}

.bar-value {
  font-size: 13px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.stock-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stock-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.empty {
  color: var(--text-faint);
  font-size: 13px;
}
</style>