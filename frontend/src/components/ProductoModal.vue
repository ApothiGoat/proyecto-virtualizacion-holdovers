<script setup>
import { computed, reactive, ref, watch } from "vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  producto: { type: Object, default: null }, // null = creando, objeto = editando
  categorias: { type: Array, default: () => [] }, // nombres de categorías existentes
  stockActual: { type: Number, default: 0 }, // solo se usa al editar
  error: { type: String, default: "" },
});

const emit = defineEmits(["close", "save", "nueva-categoria"]);

const form = reactive({
  sku: "",
  nombre: "",
  categoria: "",
  precio: "",
  stock_inicial: 0, // al crear
  ajuste_stock: 0, // al editar (+/-)
});

const agregandoCategoria = ref(false);
const nuevaCategoria = ref("");

const esEdicion = computed(() => !!props.producto);

watch(
  () => [props.open, props.producto],
  () => {
    agregandoCategoria.value = false;
    nuevaCategoria.value = "";
    form.stock_inicial = 0;
    form.ajuste_stock = 0;
    if (props.producto) {
      form.sku = props.producto.sku;
      form.nombre = props.producto.nombre;
      form.categoria = props.producto.categoria;
      form.precio = props.producto.precio;
    } else {
      form.sku = "";
      form.nombre = "";
      form.categoria = "";
      form.precio = "";
    }
  },
  { immediate: true }
);

// Si el servidor devuelve la categoría con otras mayúsculas ("electrónica" -> "Electrónica"),
// se ajusta la selección para que coincida con la opción del listado.
watch(
  () => props.categorias,
  (lista) => {
    const igual = lista.find((c) => c.toLowerCase() === String(form.categoria).toLowerCase());
    if (igual) form.categoria = igual;
  }
);

/* ---- stock ---- */

// Un solo campo visual: al crear es el stock inicial, al editar es el ajuste (+/-)
const stockCampo = computed({
  get: () => (esEdicion.value ? form.ajuste_stock : form.stock_inicial),
  set: (v) => {
    if (esEdicion.value) form.ajuste_stock = v;
    else form.stock_inicial = v;
  },
});

const minStock = computed(() => (esEdicion.value ? -props.stockActual : 0));

const stockResultante = computed(() => props.stockActual + Number(form.ajuste_stock || 0));

const stockValido = computed(() => {
  const valor = Number(stockCampo.value || 0);
  if (!Number.isInteger(valor)) return false;
  return esEdicion.value ? props.stockActual + valor >= 0 : valor >= 0;
});

function sumarStock() {
  stockCampo.value = Number(stockCampo.value || 0) + 1;
}

function restarStock() {
  stockCampo.value = Math.max(minStock.value, Number(stockCampo.value || 0) - 1);
}

/* ---- categoría ---- */

function confirmarNuevaCategoria() {
  const valor = nuevaCategoria.value.trim();
  if (!valor) return;
  emit("nueva-categoria", valor); // el padre la guarda en el catálogo
  form.categoria = valor;
  nuevaCategoria.value = "";
  agregandoCategoria.value = false;
}

function submit() {
  if (!stockValido.value) return;
  emit("save", {
    sku: form.sku.trim(),
    nombre: form.nombre,
    categoria: form.categoria,
    precio: Number(form.precio),
    ...(esEdicion.value
      ? { ajuste_stock: Number(form.ajuste_stock || 0) }
      : { stock_inicial: Number(form.stock_inicial || 0) }),
  });
}
</script>

<template>
  <div v-if="open" class="overlay" @click.self="$emit('close')">
    <div
      class="modal card"
      role="dialog"
      aria-modal="true"
      :aria-label="esEdicion ? 'Editar producto' : 'Nuevo producto'"
    >
      <div class="modal-head">
        <h2>{{ esEdicion ? "Editar producto" : "Nuevo producto" }}</h2>
        <button class="btn-icon" aria-label="Cerrar" @click="$emit('close')">✕</button>
      </div>

      <form class="modal-body" @submit.prevent="submit">
        <div class="field">
          <label for="p-sku">SKU</label>
          <input id="p-sku" v-model="form.sku" :disabled="esEdicion" placeholder="EJ-0001" required />
        </div>

        <div class="field">
          <label for="p-nombre">Nombre</label>
          <input id="p-nombre" v-model="form.nombre" placeholder="Nombre del producto" required />
        </div>

        <div class="field">
          <label for="p-categoria">Categoría</label>
          <div v-if="!agregandoCategoria" class="categoria-row">
            <select id="p-categoria" v-model="form.categoria" required>
              <option value="" disabled>Elegí una categoría</option>
              <option v-for="c in categorias" :key="c" :value="c">{{ c }}</option>
            </select>
            <button
              type="button"
              class="btn-icon"
              aria-label="Agregar categoría"
              title="Agregar categoría"
              @click="agregandoCategoria = true"
            >
              +
            </button>
          </div>
          <div v-else class="categoria-row">
            <input
              v-model="nuevaCategoria"
              placeholder="Nombre de la categoría"
              maxlength="60"
              @keyup.enter.prevent="confirmarNuevaCategoria"
            />
            <button type="button" class="btn-icon" aria-label="Confirmar categoría" @click="confirmarNuevaCategoria">
              ✓
            </button>
            <button type="button" class="btn-icon" aria-label="Cancelar" @click="agregandoCategoria = false">
              ✕
            </button>
          </div>
        </div>

        <div class="row">
          <div class="field">
            <label for="p-precio">Precio (Q)</label>
            <input
              id="p-precio"
              v-model="form.precio"
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              required
            />
          </div>

          <div class="field">
            <label for="p-stock">{{ esEdicion ? "Ajustar stock (+ / −)" : "Stock inicial" }}</label>
            <div class="qty">
              <input id="p-stock" v-model.number="stockCampo" type="number" :min="minStock" step="1" />
              <div class="stepper">
                <button type="button" class="stepper-btn" aria-label="Aumentar" @click="sumarStock">▲</button>
                <button type="button" class="stepper-btn" aria-label="Disminuir" @click="restarStock">▼</button>
              </div>
            </div>
          </div>
        </div>

        <p v-if="esEdicion" class="hint" :class="{ 'hint-error': !stockValido }">
          <template v-if="stockValido">
            Stock actual: {{ stockActual }} · quedará en {{ stockResultante }}
          </template>
          <template v-else>El stock no puede quedar por debajo de 0 (actual: {{ stockActual }}).</template>
        </p>
        <p v-else-if="!stockValido" class="hint hint-error">El stock inicial debe ser un entero de 0 o más.</p>

        <p v-if="error" class="alert-error" role="alert">{{ error }}</p>

        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="$emit('close')">Cancelar</button>
          <button type="submit" class="btn btn-primary" :disabled="!stockValido">
            {{ esEdicion ? "Guardar cambios" : "Crear producto" }}
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
  width: min(460px, 92vw);
  max-height: 92vh;
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
  gap: 16px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.categoria-row {
  display: flex;
  gap: 6px;
}

.categoria-row select,
.categoria-row input {
  flex: 1;
  min-width: 0;
}

.categoria-row .btn-icon {
  flex-shrink: 0;
  border: 1px solid var(--border);
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

.hint {
  margin: -6px 0 0;
  font-size: 12px;
  color: var(--text-faint);
}

.hint-error {
  color: var(--danger);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: none;
}
</style>