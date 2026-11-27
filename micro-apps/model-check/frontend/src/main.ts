import "./styles.css";
import { api, type CatalogSnapshot, type Model, type ProviderInfo } from "./api";

type SortKey = "id" | "input" | "output" | "context" | "released";
type TabKey = "visible" | "hidden";

const ROW_HEIGHT = 48;
const OVERSCAN = 10;
const QUICK_TAGS = ["reasoning", "tool-use", "vision", "open-weights", "free", "fast"];

interface State {
  providers: ProviderInfo[];
  activeProvider: string;
  snapshot: CatalogSnapshot | null;
  tab: TabKey;
  search: string;
  selectedType: string;
  selectedTag: string;
  sortBy: SortKey;
  selectedModelId: string | null;
  loading: boolean;
  error: string | null;
  filtered: Model[];
}

const state: State = {
  providers: [],
  activeProvider: "vercel",
  snapshot: null,
  tab: "visible",
  search: "",
  selectedType: "all",
  selectedTag: "",
  sortBy: "id",
  selectedModelId: null,
  loading: true,
  error: null,
  filtered: [],
};

// Cached DOM refs for fast incremental updates without full re-renders.
let els: {
  providerSelect: HTMLSelectElement;
  searchInput: HTMLInputElement;
  tabVisibleBtn: HTMLButtonElement;
  tabHiddenBtn: HTMLButtonElement;
  visibleCount: HTMLSpanElement;
  hiddenCount: HTMLSpanElement;
  refreshBtn: HTMLButtonElement;
  sourceBadge: HTMLSpanElement;
  errorBox: HTMLDivElement;
  typePills: HTMLDivElement;
  tagPills: HTMLDivElement;
  sortSelect: HTMLSelectElement;
  statusText: HTMLSpanElement;
  viewport: HTMLDivElement;
  spacer: HTMLDivElement;
  rowsLayer: HTMLDivElement;
  emptyState: HTMLDivElement;
  drawer: HTMLElement;
};

function fmtContext(n: number): string {
  if (!n || n <= 0) return "-";
  if (n >= 1_000_000) return `${Number((n / 1_000_000).toPrecision(3))}M`;
  if (n >= 1_000) return `${Number((n / 1_000).toPrecision(3))}K`;
  return String(n);
}

function fmtDate(epochSec: number): string {
  if (!epochSec) return "-";
  const d = new Date(epochSec * 1000);
  if (Number.isNaN(d.getTime())) return "-";
  return d.toISOString().slice(0, 10);
}

function fmtPerM(v?: number): string {
  if (v === undefined || v === null) return "-";
  if (v === 0) return "Free";
  const trimmed = v.toFixed(4).replace(/0+$/, "");
  const [w, f = ""] = trimmed.split(".");
  return `$${w}.${f.padEnd(2, "0")}`;
}

function escapeHTML(s: string): string {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function recomputeFiltered(): void {
  const models = state.snapshot?.models ?? [];
  const q = state.search.trim().toLowerCase();
  const wantHidden = state.tab === "hidden";

  const out = models.filter((m) => {
    if (m.hidden !== wantHidden) return false;
    if (state.selectedType !== "all" && m.type !== state.selectedType) return false;
    if (state.selectedTag && !m.tags.includes(state.selectedTag)) return false;
    if (q) {
      return (
        m.id.toLowerCase().includes(q) ||
        m.name.toLowerCase().includes(q) ||
        m.ownedBy.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const priceOrInf = (v?: number) => (v === undefined || v === null || v < 0 ? Number.POSITIVE_INFINITY : v);

  out.sort((a, b) => {
    switch (state.sortBy) {
      case "input":
        return priceOrInf(a.pricing.inputPerMillion) - priceOrInf(b.pricing.inputPerMillion) || a.id.localeCompare(b.id);
      case "output":
        return priceOrInf(a.pricing.outputPerMillion) - priceOrInf(b.pricing.outputPerMillion) || a.id.localeCompare(b.id);
      case "context":
        return b.contextWindow - a.contextWindow || a.id.localeCompare(b.id);
      case "released":
        return b.released - a.released || a.id.localeCompare(b.id);
      case "id":
      default:
        return a.id.localeCompare(b.id);
    }
  });

  state.filtered = out;
}

function renderVirtualRows(): void {
  const total = state.filtered.length;
  els.statusText.textContent = state.loading
    ? "Loading catalog..."
    : `Showing ${total} ${state.tab === "hidden" ? "hidden" : "visible"} model${total === 1 ? "" : "s"}`;

  if (total === 0) {
    els.spacer.style.height = "0px";
    els.rowsLayer.innerHTML = "";
    els.emptyState.style.display = "flex";
    els.emptyState.textContent = state.loading
      ? "Loading Vercel AI Gateway models..."
      : state.tab === "hidden"
        ? "No hidden models match the current filters."
        : "No models match the current filters.";
    return;
  }

  els.emptyState.style.display = "none";
  els.spacer.style.height = `${total * ROW_HEIGHT}px`;

  const scrollTop = els.viewport.scrollTop;
  const viewHeight = els.viewport.clientHeight || 600;
  const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
  const end = Math.min(total, Math.ceil((scrollTop + viewHeight) / ROW_HEIGHT) + OVERSCAN);

  els.rowsLayer.style.transform = `translateY(${start * ROW_HEIGHT}px)`;

  const parts: string[] = [];
  for (let i = start; i < end; i++) {
    const m = state.filtered[i];
    const [owner, ...rest] = m.id.split("/");
    const modelPart = rest.length ? rest.join("/") : owner;
    const idHtml = rest.length
      ? `<span class="model-owner">${escapeHTML(owner)}/</span>${escapeHTML(modelPart)}`
      : escapeHTML(m.id);

    const inClass = m.pricing.inputDisplay === "Free" ? "price-free" : m.pricing.inputDisplay === "-" ? "price-muted" : "";
    const outClass = m.pricing.outputDisplay === "Free" ? "price-free" : m.pricing.outputDisplay === "-" ? "price-muted" : "";
    const mods = m.inputMods.length || m.outputMods.length
      ? `${m.inputMods.join(",")} → ${m.outputMods.join(",")}`
      : "-";
    const selectedCls = m.id === state.selectedModelId ? " selected" : "";
    const actionLabel = m.hidden ? "Unhide" : "Hide";
    const actionAttr = m.hidden ? "unhide" : "hide";

    parts.push(`
      <div class="row grid-cols${selectedCls}" data-id="${escapeHTML(m.id)}">
        <div class="model-cell">
          <div class="model-id">${idHtml}</div>
          <div class="model-sub">${escapeHTML(m.name)}</div>
        </div>
        <div><span class="type-badge ${escapeHTML(m.type)}">${escapeHTML(m.type || "-")}</span></div>
        <div class="num price-cell ${inClass}">${escapeHTML(m.pricing.inputDisplay)}</div>
        <div class="num price-cell ${outClass}">${escapeHTML(m.pricing.outputDisplay)}</div>
        <div class="num">${escapeHTML(fmtContext(m.contextWindow))}</div>
        <div class="mods-cell" title="${escapeHTML(mods)}">${escapeHTML(mods)}</div>
        <div class="num">
          <button class="row-action" data-action="${actionAttr}" data-id="${escapeHTML(m.id)}">${actionLabel}</button>
        </div>
      </div>
    `);
  }

  els.rowsLayer.innerHTML = parts.join("");
}

function renderDrawer(): void {
  const m = state.snapshot?.models.find((x) => x.id === state.selectedModelId) ?? null;
  if (!m) {
    els.drawer.classList.add("closed");
    els.drawer.innerHTML = "";
    return;
  }

  els.drawer.classList.remove("closed");
  const actionLabel = m.hidden ? "Unhide Model" : "Hide Model";
  const actionType = m.hidden ? "unhide" : "hide";
  const tagsHtml = m.tags.length
    ? m.tags.map((t) => `<span class="tag">${escapeHTML(t)}</span>`).join("")
    : `<span class="tag">none</span>`;

  els.drawer.innerHTML = `
    <div class="drawer-head">
      <div>
        <div class="drawer-title">${escapeHTML(m.name)}</div>
        <div class="drawer-id">${escapeHTML(m.id)}</div>
      </div>
      <button class="btn" data-drawer="close" title="Close (Esc)">✕</button>
    </div>

    <div class="drawer-actions">
      <button class="btn" data-drawer="copy" data-id="${escapeHTML(m.id)}">Copy ID</button>
      <button class="btn" data-drawer="${actionType}" data-id="${escapeHTML(m.id)}">${actionLabel}</button>
    </div>

    ${m.description ? `<p class="drawer-desc">${escapeHTML(m.description)}</p>` : ""}

    <div class="meta-grid">
      <div class="meta-card">
        <div class="meta-label">Input / 1M</div>
        <div class="meta-val">${escapeHTML(m.pricing.inputDisplay)}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">Output / 1M</div>
        <div class="meta-val">${escapeHTML(m.pricing.outputDisplay)}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">Cache Read / 1M</div>
        <div class="meta-val">${escapeHTML(fmtPerM(m.pricing.cacheReadPerMillion))}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">Cache Write / 1M</div>
        <div class="meta-val">${escapeHTML(fmtPerM(m.pricing.cacheWritePerMillion))}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">Context Window</div>
        <div class="meta-val">${escapeHTML(fmtContext(m.contextWindow))}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">Max Output</div>
        <div class="meta-val">${escapeHTML(fmtContext(m.maxTokens))}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">Released</div>
        <div class="meta-val">${escapeHTML(fmtDate(m.released))}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">Knowledge</div>
        <div class="meta-val">${escapeHTML(m.knowledge || "-")}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">ZDR</div>
        <div class="meta-val">${escapeHTML(m.zdr || "-")}</div>
      </div>
      <div class="meta-card">
        <div class="meta-label">No Training</div>
        <div class="meta-val">${escapeHTML(m.noTraining || "-")}</div>
      </div>
    </div>

    <div>
      <div class="meta-label" style="margin-bottom:6px;">Tags</div>
      <div class="tag-list">${tagsHtml}</div>
    </div>
  `;
}

function renderChrome(): void {
  els.providerSelect.innerHTML = state.providers
    .map(
      (p) =>
        `<option value="${escapeHTML(p.id)}"${p.id === state.activeProvider ? " selected" : ""}>${escapeHTML(p.name)}</option>`
    )
    .join("");

  const vis = state.snapshot?.visibleCount ?? 0;
  const hid = state.snapshot?.hiddenCount ?? 0;
  els.visibleCount.textContent = String(vis);
  els.hiddenCount.textContent = String(hid);
  els.tabVisibleBtn.classList.toggle("active", state.tab === "visible");
  els.tabHiddenBtn.classList.toggle("active", state.tab === "hidden");

  els.refreshBtn.disabled = state.loading;
  if (state.snapshot) {
    els.sourceBadge.textContent = state.snapshot.source;
    els.sourceBadge.className = `source-badge ${state.snapshot.source}`;
    els.sourceBadge.style.display = "inline-block";
  } else {
    els.sourceBadge.style.display = "none";
  }

  if (state.error) {
    els.errorBox.textContent = state.error;
    els.errorBox.style.display = "block";
  } else {
    els.errorBox.style.display = "none";
  }

  const types = ["all", ...(state.snapshot?.types ?? [])];
  els.typePills.innerHTML = types
    .map(
      (t) =>
        `<button class="pill${state.selectedType === t ? " active" : ""}" data-type="${escapeHTML(t)}">${escapeHTML(t === "all" ? "All types" : t)}</button>`
    )
    .join("");

  const availableTags = new Set(state.snapshot?.tags ?? []);
  const shownTags = QUICK_TAGS.filter((t) => availableTags.has(t));
  els.tagPills.innerHTML = shownTags
    .map(
      (t) =>
        `<button class="pill${state.selectedTag === t ? " active" : ""}" data-tag="${escapeHTML(t)}">${escapeHTML(t)}</button>`
    )
    .join("");
}

function updateView(resetScroll = false): void {
  recomputeFiltered();
  renderChrome();
  if (resetScroll) {
    els.viewport.scrollTop = 0;
  }
  renderVirtualRows();
  renderDrawer();
}

async function loadCatalog(refresh = false): Promise<void> {
  state.loading = true;
  state.error = null;
  renderChrome();
  renderVirtualRows();
  try {
    state.snapshot = refresh
      ? await api.refreshCatalog(state.activeProvider)
      : await api.getCatalog(state.activeProvider);
  } catch (err) {
    state.error = err instanceof Error ? err.message : String(err);
  } finally {
    state.loading = false;
    updateView(refresh);
  }
}

async function toggleHide(modelID: string, hide: boolean): Promise<void> {
  try {
    state.error = null;
    state.snapshot = hide
      ? await api.hideModel(state.activeProvider, modelID)
      : await api.unhideModel(state.activeProvider, modelID);
    updateView(false);
  } catch (err) {
    state.error = err instanceof Error ? err.message : String(err);
    renderChrome();
  }
}

function mount(): void {
  const root = document.getElementById("app")!;
  root.innerHTML = `
    <div class="shell">
      <header class="topbar">
        <div class="brand">
          <span class="brand-dot"></span>
          <span>Model Check</span>
        </div>

        <select id="providerSelect" class="select" aria-label="Provider"></select>

        <div class="search-wrap">
          <input id="searchInput" class="search-input" type="search" placeholder="Search models, owners..." />
          <span class="search-kbd">/</span>
        </div>

        <div class="segmented" role="tablist">
          <button id="tabVisible" class="seg-btn active" role="tab">Visible <span id="visibleCount" class="seg-count">0</span></button>
          <button id="tabHidden" class="seg-btn" role="tab">Hidden <span id="hiddenCount" class="seg-count">0</span></button>
        </div>

        <span id="sourceBadge" class="source-badge" style="display:none"></span>
        <button id="refreshBtn" class="btn">Refresh</button>
      </header>

      <div class="filterbar">
        <div class="pills">
          <div id="typePills" class="pills"></div>
          <span class="pill-sep"></span>
          <div id="tagPills" class="pills"></div>
        </div>
        <div class="filter-right">
          <span id="statusText" class="status-text"></span>
          <select id="sortSelect" class="select" aria-label="Sort by">
            <option value="id">Sort: Name</option>
            <option value="input">Sort: Cheapest Input</option>
            <option value="output">Sort: Cheapest Output</option>
            <option value="context">Sort: Largest Context</option>
            <option value="released">Sort: Newest</option>
          </select>
        </div>
      </div>

      <div id="errorBox" class="error-banner" style="display:none"></div>

      <div class="workspace">
        <div class="table-pane">
          <div class="list-header grid-cols">
            <div>Model</div>
            <div>Type</div>
            <div class="num">In / 1M</div>
            <div class="num">Out / 1M</div>
            <div class="num">Ctx</div>
            <div>Modalities</div>
            <div class="num">Action</div>
          </div>
          <div id="viewport" class="viewport">
            <div id="emptyState" class="empty-state"></div>
            <div id="spacer" class="spacer">
              <div id="rowsLayer" class="rows-layer"></div>
            </div>
          </div>
        </div>
        <aside id="drawer" class="drawer closed"></aside>
      </div>
    </div>
  `;

  els = {
    providerSelect: document.getElementById("providerSelect") as HTMLSelectElement,
    searchInput: document.getElementById("searchInput") as HTMLInputElement,
    tabVisibleBtn: document.getElementById("tabVisible") as HTMLButtonElement,
    tabHiddenBtn: document.getElementById("tabHidden") as HTMLButtonElement,
    visibleCount: document.getElementById("visibleCount") as HTMLSpanElement,
    hiddenCount: document.getElementById("hiddenCount") as HTMLSpanElement,
    refreshBtn: document.getElementById("refreshBtn") as HTMLButtonElement,
    sourceBadge: document.getElementById("sourceBadge") as HTMLSpanElement,
    errorBox: document.getElementById("errorBox") as HTMLDivElement,
    typePills: document.getElementById("typePills") as HTMLDivElement,
    tagPills: document.getElementById("tagPills") as HTMLDivElement,
    sortSelect: document.getElementById("sortSelect") as HTMLSelectElement,
    statusText: document.getElementById("statusText") as HTMLSpanElement,
    viewport: document.getElementById("viewport") as HTMLDivElement,
    spacer: document.getElementById("spacer") as HTMLDivElement,
    rowsLayer: document.getElementById("rowsLayer") as HTMLDivElement,
    emptyState: document.getElementById("emptyState") as HTMLDivElement,
    drawer: document.getElementById("drawer") as HTMLElement,
  };

  els.providerSelect.addEventListener("change", () => {
    state.activeProvider = els.providerSelect.value;
    state.selectedType = "all";
    state.selectedTag = "";
    state.selectedModelId = null;
    void loadCatalog(false);
  });

  els.searchInput.addEventListener("input", () => {
    state.search = els.searchInput.value;
    updateView(true);
  });

  els.tabVisibleBtn.addEventListener("click", () => {
    state.tab = "visible";
    updateView(true);
  });

  els.tabHiddenBtn.addEventListener("click", () => {
    state.tab = "hidden";
    updateView(true);
  });

  els.refreshBtn.addEventListener("click", () => {
    void loadCatalog(true);
  });

  els.sortSelect.addEventListener("change", () => {
    state.sortBy = els.sortSelect.value as SortKey;
    updateView(true);
  });

  els.typePills.addEventListener("click", (e) => {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-type]");
    if (!btn) return;
    state.selectedType = btn.dataset.type ?? "all";
    updateView(true);
  });

  els.tagPills.addEventListener("click", (e) => {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-tag]");
    if (!btn) return;
    const tag = btn.dataset.tag ?? "";
    state.selectedTag = state.selectedTag === tag ? "" : tag;
    updateView(true);
  });

  els.viewport.addEventListener("scroll", () => {
    renderVirtualRows();
  });

  window.addEventListener("resize", () => {
    renderVirtualRows();
  });

  els.rowsLayer.addEventListener("click", (e) => {
    const target = e.target as HTMLElement;
    const actionBtn = target.closest<HTMLButtonElement>("button[data-action]");
    if (actionBtn) {
      e.stopPropagation();
      const id = actionBtn.dataset.id;
      const action = actionBtn.dataset.action;
      if (id && (action === "hide" || action === "unhide")) {
        void toggleHide(id, action === "hide");
      }
      return;
    }

    const row = target.closest<HTMLElement>(".row[data-id]");
    if (row?.dataset.id) {
      state.selectedModelId = state.selectedModelId === row.dataset.id ? null : row.dataset.id;
      renderVirtualRows();
      renderDrawer();
    }
  });

  els.drawer.addEventListener("click", (e) => {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-drawer]");
    if (!btn) return;
    const action = btn.dataset.drawer;
    const id = btn.dataset.id;
    if (action === "close") {
      state.selectedModelId = null;
      renderVirtualRows();
      renderDrawer();
    } else if (action === "copy" && id) {
      void navigator.clipboard?.writeText(id).then(() => {
        btn.textContent = "Copied!";
        setTimeout(() => {
          btn.textContent = "Copy ID";
        }, 1200);
      });
    } else if ((action === "hide" || action === "unhide") && id) {
      void toggleHide(id, action === "hide");
    }
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== els.searchInput) {
      e.preventDefault();
      els.searchInput.focus();
    } else if (e.key === "Escape") {
      if (document.activeElement === els.searchInput && els.searchInput.value) {
        els.searchInput.value = "";
        state.search = "";
        updateView(true);
      } else if (state.selectedModelId) {
        state.selectedModelId = null;
        renderVirtualRows();
        renderDrawer();
      }
    }
  });
}

async function init(): Promise<void> {
  mount();
  try {
    state.providers = await api.listProviders();
    if (state.providers.length > 0 && !state.providers.some((p) => p.id === state.activeProvider)) {
      state.activeProvider = state.providers[0].id;
    }
    await loadCatalog(false);
  } catch (err) {
    state.loading = false;
    state.error = err instanceof Error ? err.message : String(err);
    renderChrome();
    renderVirtualRows();
  }
}

void init();
