<script setup>
import { computed, reactive, ref, watch } from "vue";
import { formatQ } from "../utils/format.js";

const props = defineProps({
  open: { type: Boolean, default: false },
  pedido: { type: Object, default: null }, // null = pedido nuevo, objeto = editando
  productos: { type: Array, default: () => [] }, // [{sku, nombre, precio}]
  clientes: { type: Array, default: () => [] }, // [{id, nombre}]
  error: { type: String, default: "" },
});

const emit = defineEmits(["close", "save"]);

const form = reactive({
  carne_integrante: "",
  cliente_id: "",
});

const items = ref([{ sku: "", cantidad: 1 }]);

const esEdicion = computed(() => !!props.pedido);

watch(
  () => [props.open, props.pedido],
  ([abierto]) => {
    if (!abierto) return;
    if (props.pedido) {
      form.carne_integrante = props.pedido.carne_integrante ?? "";
      form.cliente_id = props.pedido.cliente_id ?? "";
      const previos = (props.pedido.items ?? []).map((it) => ({
        sku: it.sku,
        cantidad: Number(it.cantidad),
      }));
      items.value = previos.length ? previos : [{ sku: "", cantidad: 1 }];
    } else {
      form.carne_integrante = "";
      form.cliente_id = "";
      items.value = [{ sku: "", cantidad: 1 }];
    }
  },
  { immediate: true }
);

function agregarLinea() {
  items.value.push({ sku: "", cantidad: 1 });
}

function quitarLinea(idx) {
  items.value.splice(idx, 1);
}

function sumar(it) {
  it.cantidad = Number(it.cantidad || 0) + 1;
}

function restar(it) {
  it.cantidad = Math.max(1, Number(it.cantidad || 1) - 1);
}

function precioDe(sku) {
  return Number(props.productos.find((p) => p.sku === sku)?.precio ?? 0);
}

const total = computed(() =>
  items.value.reduce((acc, it) => acc + precioDe(it.sku) * Number(it.cantidad || 0), 0)
);

function submit() {
  const itemsValidos = items.value.filter((it) => it.sku && Number(it.cantidad) > 0);
  emit("save", {
    carne_integrante: form.carne_integrante,
    cliente_id: form.cliente_id === "" ? null : form.cliente_id,
    items: itemsValidos.map((it) => ({ sku: it.sku, cantidad: Number(it.cantidad) })),
  });
}
</script>

<template>
  <div v-if="open" class="overlay" @click.self="$emit('close')">
    <div
      class="modal card"
      role="dialog"
      aria-modal="true"
      :aria-label="esEdicion ? 'Editar pedido' : 'Nuevo pedido'"
    >
      <div class="modal-head">
        <h2>{{ esEdicion ? `Editar pedido ${pedido.id}` : "Nuevo pedido" }}</h2>
        <button class="btn-icon" aria-label="Cerrar" @click="$emit('close')">✕</button>
      </div>

      <form class="modal-body" @submit.prevent="submit">
        <div class="row">
          <div class="field">
            <label for="ped-carne">Carné de quien crea el pedido</label>
            <input
              id="ped-carne"
              v-model="form.carne_integrante"
              :disabled="esEdicion"
              placeholder="0000-00-00000"
              required
            />
          </div>

          <div class="field">
            <label for="ped-cliente">Cliente (opcional)</label>
            <select id="ped-cliente" v-model="form.cliente_id">
              <option value="">Sin cliente asociado</option>
              <option v-for="c in clientes" :key="c.id" :value="c.id">{{ c.nombre }}</option>
            </select>
          </div>
        </div>

        <div class="items">
          <div class="items-head">
            <span>Producto</span>
            <span>Cantidad</span>
            <span>Subtotal</span>
            <span aria-hidden="true"></span>
          </div>

          <div v-for="(it, idx) in items" :key="idx" class="item-row">
            <select v-model="it.sku" required>
              <option value="" disabled>Elegí un producto</option>
              <option v-for="p in productos" :key="p.sku" :value="p.sku">{{ p.nombre }}</option>
            </select>

            <div class="qty">
              <input v-model.number="it.cantidad" type="number" min="1" required />
              <div class="stepper">
                <button type="button" class="stepper-btn" aria-label="Aumentar cantidad" @click="sumar(it)">▲</button>
                <button type="button" class="stepper-btn" aria-label="Disminuir cantidad" @click="restar(it)">▼</button>
              </div>
            </div>

            <span class="subtotal">{{ formatQ(precioDe(it.sku) * (it.cantidad || 0)) }}</span>

            <button
              type="button"
              class="btn-icon"
              aria-label="Quitar producto"
              :disabled="items.length === 1"
              @click="quitarLinea(idx)"
            >
              ✕
            </button>
          </div>

          <button type="button" class="btn btn-ghost add-line" @click="agregarLinea">
            + Agregar producto
          </button>
        </div>

        <div class="total-row">
          <span>Total</span>
          <span class="total-value">{{ formatQ(total) }}</span>
        </div>

        <p v-if="error" class="alert-error" role="alert">{{ error }}</p>

        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="$emit('close')">Cancelar</button>
          <button type="submit" class="btn btn-primary">
            {{ esEdicion ? "Guardar cambios" : "Generar pedido" }}
          </button>
        </div>
      </form>
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
  width: min(600px, 92vw);
  max-height: 88vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-soft);
}

.modal-body {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.items-head,
.item-row {
  display: grid;
  grid-template-columns: 1fr 112px 100px 32px;
  gap: 10px;
}

.items-head {
  font-size: 12px;
  color: var(--text-faint);
  padding: 0 2px;
}

.item-row {
  align-items: center;
}

.item-row select,
.qty input {
  width: 100%;
  min-width: 0;
  background-color: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
}

.item-row select {
  padding-right: 32px;
}

.qty {
  display: flex;
}

.qty input {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  border-right: none;
}

.qty .stepper {
  border-radius: 0 8px 8px 0;
}

.qty .stepper-btn {
  flex: 1;
}

.subtotal {
  font-size: 13px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.add-line {
  align-self: flex-start;
  padding: 8px 14px;
  font-size: 13px;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.total-value {
  color: var(--accent);
  font-family: var(--font-display);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>