<script setup>
import { computed } from "vue";
import { claseEstado, etiquetaEstado, formatFecha, formatQ } from "../utils/format.js";

const props = defineProps({
  open: { type: Boolean, default: false },
  pedido: { type: Object, default: null }, // pedido ya enriquecido: cliente_nombre + items con nombre/subtotal
});

const emit = defineEmits(["close", "editar", "cambiar-estado"]);

const esPendiente = computed(() => props.pedido?.estado === "pendiente");

const clienteTexto = computed(() => {
  const p = props.pedido;
  if (!p) return "";
  if (p.cliente_nombre) return p.cliente_nombre;
  return p.cliente_id ? `Cliente #${p.cliente_id}` : "Sin cliente asociado";
});

function marcarComoVenta() {
  emit("cambiar-estado", { id: props.pedido.id, estado: "completado" });
}

function cancelarPedido() {
  const ok = window.confirm(`¿Cancelar el pedido ${props.pedido.id}? Esta acción no se puede deshacer.`);
  if (ok) emit("cambiar-estado", { id: props.pedido.id, estado: "cancelado" });
}
</script>

<template>
  <div v-if="open && pedido" class="overlay" @click.self="$emit('close')">
    <div class="modal card" role="dialog" aria-modal="true" :aria-label="`Pedido ${pedido.id}`">
      <div class="modal-head">
        <div>
          <div class="title-row">
            <h2>Pedido {{ pedido.id }}</h2>
            <span class="badge" :class="claseEstado(pedido.estado)">{{ etiquetaEstado(pedido.estado) }}</span>
          </div>
          <p class="sub">{{ formatFecha(pedido.fecha) }} · creado por {{ pedido.carne_integrante }}</p>
        </div>
        <button class="btn-icon" aria-label="Cerrar" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <div class="summary">
          <div>
            <div class="summary-label">Cliente</div>
            <div class="summary-value">{{ clienteTexto }}</div>
          </div>
          <div class="summary-right">
            <div class="summary-label">Total</div>
            <div class="summary-total">{{ formatQ(pedido.total) }}</div>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Producto</th>
              <th>Cant.</th>
              <th>P. unitario</th>
              <th>Subtotal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in pedido.items" :key="it.sku">
              <td>{{ it.sku }}</td>
              <td>{{ it.nombre }}</td>
              <td>{{ it.cantidad }}</td>
              <td>{{ formatQ(it.precio_unitario) }}</td>
              <td>{{ formatQ(it.subtotal) }}</td>
            </tr>
          </tbody>
        </table>

        <p v-if="!esPendiente" class="closed-note">
          Este pedido está {{ pedido.estado === "cancelado" ? "cancelado" : "cerrado como venta" }} y ya no se puede modificar.
        </p>

        <div class="modal-actions">
          <button v-if="esPendiente" type="button" class="btn btn-danger cancel-btn" @click="cancelarPedido">
            Cancelar pedido
          </button>
          <button type="button" class="btn btn-ghost" @click="$emit('close')">Cerrar</button>
          <button v-if="esPendiente" type="button" class="btn btn-ghost" @click="$emit('editar')">Editar</button>
          <button v-if="esPendiente" type="button" class="btn btn-primary" @click="marcarComoVenta">
            Marcar como venta
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(6, 5, 10, 0.65);
  backdrop-filter: blur(2px);
  display: grid;
  place-items: center;
  z-index: 50;
}

.modal {
  width: min(700px, 92vw);
  max-height: 88vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 22px 28px 16px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sub {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-faint);
}

.modal-body {
  padding: 4px 28px 26px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.summary-right {
  text-align: right;
}

.summary-label {
  font-size: 13px;
  color: var(--text-faint);
  margin-bottom: 4px;
}

.summary-value {
  font-weight: 600;
  font-size: 16px;
}

.summary-total {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 18px;
  color: var(--accent);
}

.closed-note {
  margin: 0;
  font-size: 13px;
  color: var(--text-faint);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-btn {
  margin-right: auto;
}
</style>