<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import PedidoDetalleModal from "../components/PedidoDetalleModal.vue";
import PedidoFormModal from "../components/PedidoFormModal.vue";
import DatePickerField from "../components/DatePickerField.vue";
import { ESTADOS, claseEstado, etiquetaEstado, formatFecha, formatQ } from "../utils/format.js";

const pedidos = ref([]); // [{id, cliente_id, carne_integrante, fecha, estado, total, items}]
const productos = ref([]);
const clientes = ref([]);
const cargando = ref(true);
const errorMsg = ref("");

const filtros = reactive({ desde: "", hasta: "", cliente_id: "", estado: "" });

const modalDetalleAbierto = ref(false);
const pedidoSeleccionado = ref(null);

const modalFormAbierto = ref(false);
const pedidoEnEdicion = ref(null); // null = pedido nuevo
const errorForm = ref("");

// El servicio de pedidos solo conoce cliente_id / sku (los nombres viven en
// otros microservicios), así que el "join" con el nombre se hace acá en el front.
const clientesPorId = computed(() => Object.fromEntries(clientes.value.map((c) => [String(c.id), c])));
const productosPorSku = computed(() => Object.fromEntries(productos.value.map((p) => [p.sku, p])));

function nombreCliente(clienteId) {
  if (clienteId === null || clienteId === undefined) return null;
  return clientesPorId.value[String(clienteId)]?.nombre ?? null;
}

const pedidosVista = computed(() =>
  pedidos.value
    .filter((p) => !filtros.estado || p.estado === filtros.estado)
    .map((p) => ({ ...p, cliente_nombre: p.cliente_nombre ?? nombreCliente(p.cliente_id) }))
);

function enriquecerPedido(data) {
  return {
    ...data,
    cliente_nombre: data.cliente_nombre ?? nombreCliente(data.cliente_id),
    items: (data.items ?? []).map((it) => ({
      ...it,
      nombre: it.nombre ?? productosPorSku.value[it.sku]?.nombre ?? it.sku,
      subtotal: Number(it.cantidad) * Number(it.precio_unitario),
    })),
  };
}

async function cargarCatalogos() {
  try {
    const [productosRes, clientesRes] = await Promise.all([
      fetch("/api/catalogo/productos").then((r) => r.json()),
      fetch("/api/clientes").then((r) => r.json()),
    ]);
    productos.value = productosRes;
    clientes.value = clientesRes;
  } catch (e) {
    console.error("No se pudieron cargar productos/clientes", e);
  }
}

async function cargar() {
  cargando.value = true;
  const params = new URLSearchParams();
  if (filtros.desde) params.set("desde", filtros.desde);
  if (filtros.hasta) params.set("hasta", filtros.hasta);
  if (filtros.cliente_id !== "") params.set("cliente_id", filtros.cliente_id);

  try {
    const res = await fetch(`/api/pedidos?${params.toString()}`);
    if (!res.ok) throw new Error("No se pudieron cargar los pedidos");
    pedidos.value = await res.json();
  } catch (e) {
    errorMsg.value = e.message;
  } finally {
    cargando.value = false;
  }
}

async function verDetalle(id) {
  try {
    const res = await fetch(`/api/pedidos/${id}`);
    if (!res.ok) throw new Error("No se pudo cargar el detalle del pedido");
    pedidoSeleccionado.value = enriquecerPedido(await res.json());
    modalDetalleAbierto.value = true;
  } catch (e) {
    errorMsg.value = e.message;
  }
}

async function cambiarEstado({ id, estado }) {
  errorMsg.value = "";
  try {
    const res = await fetch(`/api/pedidos/${id}/estado`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estado }),
    });
    const cuerpo = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(cuerpo.error ?? "No se pudo cambiar el estado");
    await Promise.all([cargar(), verDetalle(id)]);
  } catch (e) {
    errorMsg.value = e.message;
  }
}

function abrirNuevoPedido() {
  pedidoEnEdicion.value = null;
  errorForm.value = "";
  modalFormAbierto.value = true;
}

function abrirEdicion() {
  pedidoEnEdicion.value = pedidoSeleccionado.value;
  errorForm.value = "";
  modalDetalleAbierto.value = false;
  modalFormAbierto.value = true;
}

function cerrarForm() {
  modalFormAbierto.value = false;
  // si se cancela una edición, se vuelve al detalle del pedido
  if (pedidoEnEdicion.value) modalDetalleAbierto.value = true;
}

async function guardarPedido(datos) {
  errorForm.value = "";
  const editando = pedidoEnEdicion.value;
  try {
    const res = await fetch(editando ? `/api/pedidos/${editando.id}` : "/api/pedidos", {
      method: editando ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        editando ? { cliente_id: datos.cliente_id, items: datos.items } : datos
      ),
    });
    const cuerpo = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(cuerpo.error ?? "No se pudo guardar el pedido");

    modalFormAbierto.value = false;
    await cargar();
    if (editando) {
      await verDetalle(editando.id);
      pedidoEnEdicion.value = null;
    }
  } catch (e) {
    errorForm.value = e.message;
  }
}

onMounted(() => {
  cargarCatalogos();
  cargar();
});
</script>

<template>
  <div class="pedidos">
    <div class="toolbar card">
      <DatePickerField v-model="filtros.desde" label="Desde" />
      <DatePickerField v-model="filtros.hasta" label="Hasta" />

      <div class="field">
        <label for="f-cliente">Cliente</label>
        <select id="f-cliente" v-model="filtros.cliente_id">
          <option value="">Todos</option>
          <option v-for="c in clientes" :key="c.id" :value="c.id">{{ c.nombre }}</option>
        </select>
      </div>

      <div class="field">
        <label for="f-estado">Estado</label>
        <select id="f-estado" v-model="filtros.estado">
          <option value="">Todos</option>
          <option v-for="e in ESTADOS" :key="e.valor" :value="e.valor">{{ e.etiqueta }}</option>
        </select>
      </div>

      <button class="btn btn-primary filter-btn" @click="cargar">Filtrar</button>
      <button class="btn btn-primary" @click="abrirNuevoPedido">+ Nuevo pedido</button>
    </div>

    <p v-if="errorMsg" class="alert-error" role="alert">{{ errorMsg }}</p>

    <div class="card table-card">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Cliente</th>
            <th>Creado por</th>
            <th>Fecha</th>
            <th>Estado</th>
            <th>Total</th>
            <th aria-label="Acciones"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in pedidosVista" :key="p.id">
            <td>{{ p.id }}</td>
            <td>{{ p.cliente_nombre ?? "—" }}</td>
            <td>{{ p.carne_integrante }}</td>
            <td>{{ formatFecha(p.fecha) }}</td>
            <td>
              <span class="badge" :class="claseEstado(p.estado)">{{ etiquetaEstado(p.estado) }}</span>
            </td>
            <td>{{ formatQ(p.total) }}</td>
            <td class="actions">
              <button class="btn btn-ghost btn-sm" @click="verDetalle(p.id)">Ver detalle</button>
            </td>
          </tr>
          <tr v-if="!cargando && pedidosVista.length === 0">
            <td colspan="7" class="empty">No hay pedidos para los filtros seleccionados.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <PedidoDetalleModal
      :open="modalDetalleAbierto"
      :pedido="pedidoSeleccionado"
      @close="modalDetalleAbierto = false"
      @editar="abrirEdicion"
      @cambiar-estado="cambiarEstado"
    />

    <PedidoFormModal
      :open="modalFormAbierto"
      :pedido="pedidoEnEdicion"
      :productos="productos"
      :clientes="clientes"
      :error="errorForm"
      @close="cerrarForm"
      @save="guardarPedido"
    />
  </div>
</template>

<style scoped>
.pedidos {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.toolbar {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  padding: 16px 20px;
}

.toolbar .field select {
  width: 200px;
}

.filter-btn {
  margin-left: auto;
}

.table-card {
  padding: 8px 0;
  overflow-x: auto;
}

.actions {
  text-align: right;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.empty {
  text-align: center;
  color: var(--text-faint);
  padding: 32px 16px;
}
</style>