<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" }, // 'YYYY-MM-DD' o ''
  label: { type: String, default: "" },
});

const emit = defineEmits(["update:modelValue"]);

const abierto = ref(false);
const hoy = new Date();
const vista = ref(parseISO(props.modelValue) ?? new Date(hoy.getFullYear(), hoy.getMonth(), 1));

const DIAS = ["DO", "LU", "MA", "MI", "JU", "VI", "SA"];
const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

function parseISO(iso) {
  if (!iso) return null;
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function toISO(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

const etiqueta = computed(() => {
  const d = parseISO(props.modelValue);
  if (!d) return "dd/mm/aaaa";
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
});

const tituloMes = computed(() => `${MESES[vista.value.getMonth()]} de ${vista.value.getFullYear()}`);

const dias = computed(() => {
  const year = vista.value.getFullYear();
  const month = vista.value.getMonth();
  const primerDia = new Date(year, month, 1).getDay();
  const totalDias = new Date(year, month + 1, 0).getDate();
  const totalDiasMesAnterior = new Date(year, month, 0).getDate();

  const celdas = [];
  for (let i = primerDia - 1; i >= 0; i--) {
    celdas.push({ dia: totalDiasMesAnterior - i, fueraDeMes: true, date: new Date(year, month - 1, totalDiasMesAnterior - i) });
  }
  for (let d = 1; d <= totalDias; d++) {
    celdas.push({ dia: d, fueraDeMes: false, date: new Date(year, month, d) });
  }
  while (celdas.length % 7 !== 0) {
    const n = celdas.length - (primerDia + totalDias) + 1;
    celdas.push({ dia: n, fueraDeMes: true, date: new Date(year, month + 1, n) });
  }
  return celdas;
});

function esSeleccionado(date) {
  const sel = parseISO(props.modelValue);
  return sel && sel.toDateString() === date.toDateString();
}

function esHoy(date) {
  return date.toDateString() === hoy.toDateString();
}

function elegir(celda) {
  emit("update:modelValue", toISO(celda.date));
  abierto.value = false;
}

function mesAnterior() {
  vista.value = new Date(vista.value.getFullYear(), vista.value.getMonth() - 1, 1);
}
function mesSiguiente() {
  vista.value = new Date(vista.value.getFullYear(), vista.value.getMonth() + 1, 1);
}

function irAHoy() {
  vista.value = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  emit("update:modelValue", toISO(hoy));
  abierto.value = false;
}

function borrar() {
  emit("update:modelValue", "");
  abierto.value = false;
}

watch(
  () => props.modelValue,
  (val) => {
    const d = parseISO(val);
    if (d) vista.value = new Date(d.getFullYear(), d.getMonth(), 1);
  }
);
</script>

<template>
  <div class="date-field field">
    <label v-if="label">{{ label }}</label>
    <button type="button" class="date-trigger" @click="abierto = !abierto">
      <span :class="{ placeholder: !modelValue }">{{ etiqueta }}</span>
      <svg class="cal-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <rect x="3" y="4.5" width="14" height="12" rx="2" stroke="currentColor" stroke-width="1.4" />
        <path d="M3 8h14" stroke="currentColor" stroke-width="1.4" />
        <path d="M6.5 2.5v3M13.5 2.5v3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
      </svg>
    </button>

    <div v-if="abierto" class="popover card">
      <div class="popover-head">
        <span class="mes-titulo">{{ tituloMes }}</span>
        <div class="stepper">
          <button type="button" class="stepper-btn" aria-label="Mes anterior" @click="mesAnterior">▲</button>
          <button type="button" class="stepper-btn" aria-label="Mes siguiente" @click="mesSiguiente">▼</button>
        </div>
      </div>

      <div class="weekdays">
        <span v-for="d in DIAS" :key="d">{{ d }}</span>
      </div>

      <div class="days">
        <button
          v-for="(celda, i) in dias"
          :key="i"
          type="button"
          class="day"
          :class="{
            'fuera-de-mes': celda.fueraDeMes,
            hoy: esHoy(celda.date) && !esSeleccionado(celda.date),
            seleccionado: esSeleccionado(celda.date),
          }"
          @click="elegir(celda)"
        >
          {{ celda.dia }}
        </button>
      </div>

      <div class="popover-footer">
        <button type="button" class="link-btn" @click="borrar">Borrar</button>
        <button type="button" class="link-btn" @click="irAHoy">Hoy</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.date-field {
  position: relative;
}

.date-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 160px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  color: var(--text);
  font-size: 14px;
}

.date-trigger .placeholder {
  color: var(--text-faint);
}

.cal-icon {
  width: 16px;
  height: 16px;
  color: #fff;
  flex-shrink: 0;
}

.popover {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 60;
  width: 260px;
  padding: 16px;
  box-shadow: var(--shadow-modal);
}

.popover-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.mes-titulo {
  font-size: 13px;
  font-weight: 600;
  text-transform: capitalize;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 6px;
}

.weekdays span {
  font-size: 11px;
  color: var(--text-faint);
  text-align: center;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.day {
  background: transparent;
  border: none;
  color: var(--text);
  font-size: 12px;
  padding: 6px 0;
  border-radius: 6px;
}

.day:hover {
  background: var(--surface-hover);
}

.day.fuera-de-mes {
  color: var(--text-faint);
  opacity: 0.5;
}

.day.hoy {
  border: 1px solid var(--accent);
}

.day.seleccionado {
  background: var(--accent-gradient);
  color: #fff;
  font-weight: 600;
}

.popover-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-soft);
}

.link-btn {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
  padding: 0;
}

.link-btn:hover {
  filter: brightness(1.2);
}
</style>
