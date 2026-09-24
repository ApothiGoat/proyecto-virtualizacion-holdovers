<script setup>
import { RouterLink, useRoute } from "vue-router";

const route = useRoute();

const nav = [
  { to: "/", label: "Dashboard", icon: "grid" },
  { to: "/inventario", label: "Inventario", icon: "box" },
  { to: "/pedidos", label: "Pedidos", icon: "list" },
];

function isActive(to) {
  return route.path === to;
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">EQ</span>
        <div>
          <div class="brand-name">El Quetzal</div>
          <div class="brand-sub">Panel de operaciones</div>
        </div>
      </div>

      <nav class="nav">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
        >
          <span class="nav-dot" />
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <div class="main">
      <header class="topbar">
        <h1>{{ nav.find((n) => isActive(n.to))?.label ?? "El Quetzal" }}</h1>
      </header>
      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 260px 1fr;
  min-height: 100vh;
}

.sidebar {
  background: var(--bg-elevated);
  border-right: 1px solid var(--border-soft);
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 6px;
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--accent-gradient);
  color: #fff;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 13px;
  display: grid;
  place-items: center;
}

.brand-name {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 15px;
}

.brand-sub {
  font-size: 12px;
  color: var(--text-faint);
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.nav-item.active {
  background: var(--accent-soft);
  color: var(--text);
}

.nav-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.6;
}

.nav-item.active .nav-dot {
  background: var(--accent);
  opacity: 1;
}

.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  padding: 28px 40px 0;
}

.content {
  padding: 24px 40px 48px;
  flex: 1;
}
</style>
