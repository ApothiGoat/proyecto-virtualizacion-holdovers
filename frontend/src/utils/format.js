export const ESTADOS = [
  { valor: "pendiente", etiqueta: "Pendiente" },
  { valor: "completado", etiqueta: "Vendido" },
  { valor: "cancelado", etiqueta: "Cancelado" },
];

export function etiquetaEstado(estado) {
  return ESTADOS.find((e) => e.valor === estado)?.etiqueta ?? estado ?? "—";
}

export function claseEstado(estado) {
  if (estado === "cancelado") return "badge-danger";
  if (estado === "completado") return "badge-ok";
  return "badge-warn"; // pendiente / desconocido
}

export function formatQ(valor) {
  return `Q ${Number(valor ?? 0).toLocaleString("es-GT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

// La API devuelve la fecha en UTC ("Thu, 24 Sep 2026 12:42:16 GMT"); se muestra
// en hora de Guatemala como dd/mm/aaaa hh:mm.
export function formatFecha(valor) {
  if (!valor) return "—";
  const d = new Date(valor);
  if (Number.isNaN(d.getTime())) return String(valor);
  return new Intl.DateTimeFormat("es-GT", {
    timeZone: "America/Guatemala",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  })
    .format(d)
    .replace(",", "");
}