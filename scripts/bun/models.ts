#!/usr/bin/env bun
/**
 * Model browser & persistent hide manager for Vercel AI Gateway and OpenRouter.
 *
 * Syncs with:
 *   - vercel/model-updates/{models.json,hidden_models.json}
 *   - openrouter/model-updates/{models.json,hidden_models.json,allowed_models.json}
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { stdout as output } from "node:process";

type ProviderId = "vercel" | "openrouter";
type ProviderFilter = ProviderId | "all";
type SortField = "id" | "input" | "output" | "context";

interface NormalizedModel {
  provider: ProviderId;
  id: string;
  slug: string;
  name: string;
  inputPrice: number | null; // $ per 1M tokens (or null)
  outputPrice: number | null; // $ per 1M tokens (or null)
  priceLabel: string;
  inputLabel: string;
  outputLabel: string;
  contextLength: number | null;
  inMods: string[];
  outMods: string[];
  hidden: boolean;
  allowlisted: boolean;
}

interface ProviderConfig {
  id: ProviderId;
  label: string;
  apiUrl: string;
  modelsFile: string;
  hiddenFile: string;
  allowedFile: string;
}

const SCRIPT_DIR = dirname(Bun.main);
const REPO_ROOT = resolve(SCRIPT_DIR, "../..");

const PROVIDERS: Record<ProviderId, ProviderConfig> = {
  vercel: {
    id: "vercel",
    label: "Vercel AI Gateway",
    apiUrl: "https://ai-gateway.vercel.sh/v1/models",
    modelsFile: resolve(REPO_ROOT, "vercel/model-updates/models.json"),
    hiddenFile: resolve(REPO_ROOT, "vercel/model-updates/hidden_models.json"),
    allowedFile: resolve(REPO_ROOT, "vercel/model-updates/allowed_models.json"),
  },
  openrouter: {
    id: "openrouter",
    label: "OpenRouter",
    apiUrl: "https://openrouter.ai/api/v1/models",
    modelsFile: resolve(REPO_ROOT, "openrouter/model-updates/models.json"),
    hiddenFile: resolve(REPO_ROOT, "openrouter/model-updates/hidden_models.json"),
    allowedFile: resolve(REPO_ROOT, "openrouter/model-updates/allowed_models.json"),
  },
};

// ---------- ANSI helpers ----------

const useColor = output.isTTY && !process.env.NO_COLOR;
const c = {
  reset: useColor ? "\x1b[0m" : "",
  bold: useColor ? "\x1b[1m" : "",
  dim: useColor ? "\x1b[2m" : "",
  cyan: useColor ? "\x1b[36m" : "",
  green: useColor ? "\x1b[32m" : "",
  yellow: useColor ? "\x1b[33m" : "",
  magenta: useColor ? "\x1b[35m" : "",
  red: useColor ? "\x1b[31m" : "",
  gray: useColor ? "\x1b[90m" : "",
};

// ---------- pricing & formatting (matches shared/modelmd.py) ----------

function parsePricePerMillion(raw: unknown, perMillion = true): number | null {
  if (raw === null || raw === undefined || raw === "") return null;
  const num = Number(raw);
  if (!Number.isFinite(num)) return null;
  return perMillion ? num * 1_000_000 : num;
}

function fmtPrice(raw: unknown, perMillion = true): string | null {
  const val = parsePricePerMillion(raw, perMillion);
  if (val === null) return null;
  if (val < 0) return "varies";
  if (val === 0) return "Free";

  const trimmed = val.toFixed(4).replace(/0+$/, "");
  const [whole, frac = ""] = trimmed.split(".");
  return `$${whole}.${frac.padEnd(2, "0")}`;
}

function fmtContext(n: number | null): string {
  if (!n || n <= 0) return "-";
  if (n >= 1_000_000) return `${Number((n / 1_000_000).toPrecision(3))}M`;
  if (n >= 1_000) return `${Number((n / 1_000).toPrecision(3))}K`;
  return String(n);
}

function baseVercelPrice(pricing: Record<string, any>, key: string): unknown {
  if (pricing[key] !== undefined && pricing[key] !== null) {
    return pricing[key];
  }
  const tiers = pricing[`${key}_tiers`];
  if (Array.isArray(tiers) && tiers.length > 0) {
    return tiers[0]?.cost ?? null;
  }
  return null;
}

// ---------- state file I/O ----------

function loadJsonList(filePath: string): string[] {
  if (!existsSync(filePath)) return [];
  try {
    const parsed = JSON.parse(readFileSync(filePath, "utf-8"));
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string") : [];
  } catch {
    return [];
  }
}

function saveJsonList(filePath: string, items: Iterable<string>): void {
  const sorted = Array.from(new Set(items)).sort((a, b) => a.localeCompare(b));
  writeFileSync(filePath, JSON.stringify(sorted, null, 2) + "\n", "utf-8");
}

// ---------- catalog fetching & normalization ----------

async function fetchCatalog(
  cfg: ProviderConfig,
  localOnly: boolean
): Promise<{ raw: any[]; source: "live" | "local" }> {
  if (!localOnly) {
    try {
      const res = await fetch(cfg.apiUrl, {
        headers: { Accept: "application/json" },
        signal: AbortSignal.timeout(10_000),
      });
      if (res.ok) {
        const json = (await res.json()) as { data?: any[] };
        if (Array.isArray(json.data)) {
          return { raw: json.data, source: "live" };
        }
      }
    } catch {
      // Fallback to local repo snapshot below
    }
  }

  if (existsSync(cfg.modelsFile)) {
    const json = JSON.parse(readFileSync(cfg.modelsFile, "utf-8")) as { data?: any[] };
    return { raw: Array.isArray(json.data) ? json.data : [], source: "local" };
  }

  throw new Error(
    `Could not fetch ${cfg.label} live API and local snapshot not found at ${cfg.modelsFile}`
  );
}

function normalizeVercel(
  m: any,
  hiddenSet: Set<string>,
  allowedSet: Set<string>
): NormalizedModel | null {
  const id = String(m?.id ?? "");
  if (!id) return null;

  const pricing = m?.pricing ?? {};
  const rawIn = baseVercelPrice(pricing, "input");
  const rawOut = baseVercelPrice(pricing, "output");

  const pIn = fmtPrice(rawIn);
  const pOut = fmtPrice(rawOut);
  const imgPrice = pricing.image !== undefined && pricing.image !== null
    ? fmtPrice(pricing.image, false)
    : null;

  let priceLabel = "-";
  if (pIn !== null || pOut !== null) {
    priceLabel = pIn === "Free" && pOut === "Free" ? "Free" : `${pIn ?? "-"} -> ${pOut ?? "-"}`;
  } else if (imgPrice) {
    priceLabel = `${imgPrice}/img`;
  }

  const mods = m?.modalities ?? {};
  const allowlisted = allowedSet.has(id);
  const hidden = !allowlisted && hiddenSet.has(id);

  return {
    provider: "vercel",
    id,
    slug: id,
    name: String(m?.name ?? id),
    inputPrice: parsePricePerMillion(rawIn),
    outputPrice: parsePricePerMillion(rawOut),
    priceLabel,
    inputLabel: pIn ?? (imgPrice ? `${imgPrice}/img` : "-"),
    outputLabel: pOut ?? "-",
    contextLength: typeof m?.context_window === "number" ? m.context_window : null,
    inMods: Array.isArray(mods.input) ? mods.input : [],
    outMods: Array.isArray(mods.output) ? mods.output : [],
    hidden,
    allowlisted,
  };
}

function normalizeOpenRouter(
  m: any,
  hiddenSet: Set<string>,
  allowedSet: Set<string>
): NormalizedModel | null {
  const id = String(m?.id ?? m?.canonical_slug ?? "");
  if (!id) return null;
  const slug = String(m?.canonical_slug ?? id);

  const pricing = m?.pricing ?? {};
  const rawIn = pricing.prompt;
  const rawOut = pricing.completion;
  const pIn = fmtPrice(rawIn);
  const pOut = fmtPrice(rawOut);

  let priceLabel = "-";
  if (pIn !== null || pOut !== null) {
    priceLabel = pIn === "Free" && pOut === "Free" ? "Free" : `${pIn ?? "-"} -> ${pOut ?? "-"}`;
  }

  const arch = m?.architecture ?? {};
  let inMods: string[] = Array.isArray(arch.input_modalities) ? arch.input_modalities : [];
  let outMods: string[] = Array.isArray(arch.output_modalities) ? arch.output_modalities : [];
  if ((!inMods.length || !outMods.length) && typeof arch.modality === "string") {
    const [left = "", right = ""] = arch.modality.split("->");
    if (!inMods.length) inMods = left.split("+").filter(Boolean);
    if (!outMods.length) outMods = right.split("+").filter(Boolean);
  }

  const allowlisted = allowedSet.has(id) || allowedSet.has(slug);
  const hidden = !allowlisted && (hiddenSet.has(id) || hiddenSet.has(slug));

  return {
    provider: "openrouter",
    id,
    slug,
    name: String(m?.name ?? id),
    inputPrice: parsePricePerMillion(rawIn),
    outputPrice: parsePricePerMillion(rawOut),
    priceLabel,
    inputLabel: pIn ?? "-",
    outputLabel: pOut ?? "-",
    contextLength: typeof m?.context_length === "number" ? m.context_length : null,
    inMods,
    outMods,
    hidden,
    allowlisted,
  };
}

async function loadAllModels(
  providerFilter: ProviderFilter,
  localOnly: boolean
): Promise<{ models: NormalizedModel[]; sources: Partial<Record<ProviderId, "live" | "local">> }> {
  const targets: ProviderId[] =
    providerFilter === "all" ? ["vercel", "openrouter"] : [providerFilter];

  const results = await Promise.all(
    targets.map(async (pid) => {
      const cfg = PROVIDERS[pid];
      const hiddenSet = new Set(loadJsonList(cfg.hiddenFile));
      const allowedSet = new Set(loadJsonList(cfg.allowedFile));
      const { raw, source } = await fetchCatalog(cfg, localOnly);
      const normalized = raw
        .map((m) =>
          pid === "vercel"
            ? normalizeVercel(m, hiddenSet, allowedSet)
            : normalizeOpenRouter(m, hiddenSet, allowedSet)
        )
        .filter((m): m is NormalizedModel => m !== null);
      return { pid, source, normalized };
    })
  );

  const sources: Partial<Record<ProviderId, "live" | "local">> = {};
  const models: NormalizedModel[] = [];
  for (const r of results) {
    sources[r.pid] = r.source;
    models.push(...r.normalized);
  }
  return { models, sources };
}

// ---------- sorting & filtering ----------

function filterModels(models: NormalizedModel[], search?: string): NormalizedModel[] {
  if (!search) return models;
  const q = search.toLowerCase();
  return models.filter(
    (m) =>
      m.id.toLowerCase().includes(q) ||
      m.slug.toLowerCase().includes(q) ||
      m.name.toLowerCase().includes(q) ||
      m.provider.includes(q)
  );
}

function sortModels(models: NormalizedModel[], sortBy: SortField): NormalizedModel[] {
  const copy = [...models];
  const numOrInf = (v: number | null) => (v === null || v < 0 ? Number.POSITIVE_INFINITY : v);

  copy.sort((a, b) => {
    switch (sortBy) {
      case "input":
        return numOrInf(a.inputPrice) - numOrInf(b.inputPrice) || a.id.localeCompare(b.id);
      case "output":
        return numOrInf(a.outputPrice) - numOrInf(b.outputPrice) || a.id.localeCompare(b.id);
      case "context":
        return (b.contextLength ?? -1) - (a.contextLength ?? -1) || a.id.localeCompare(b.id);
      case "id":
      default:
        return a.provider.localeCompare(b.provider) || a.id.localeCompare(b.id);
    }
  });
  return copy;
}

// ---------- table rendering ----------

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.slice(0, Math.max(1, max - 1)) + "…";
}

function renderTable(rows: NormalizedModel[], limit?: number): void {
  if (rows.length === 0) {
    console.log(`  ${c.dim}(none)${c.reset}`);
    return;
  }

  const display = limit && limit > 0 ? rows.slice(0, limit) : rows;
  const maxIdWidth = Math.min(
    48,
    Math.max(10, ...display.map((m) => m.id.length))
  );
  const maxInWidth = Math.max(10, ...display.map((m) => m.inputLabel.length));
  const maxOutWidth = Math.max(11, ...display.map((m) => m.outputLabel.length));

  const header = [
    "Provider".padEnd(10),
    "Model ID".padEnd(maxIdWidth),
    "In / 1M".padStart(maxInWidth),
    "Out / 1M".padStart(maxOutWidth),
    "Ctx".padStart(6),
    "Modalities",
  ].join("  ");

  console.log(`  ${c.bold}${header}${c.reset}`);
  console.log(`  ${c.dim}${"─".repeat(header.length + 6)}${c.reset}`);

  for (const m of display) {
    const provTag =
      m.provider === "vercel"
        ? `${c.cyan}${"vercel".padEnd(10)}${c.reset}`
        : `${c.magenta}${"openrouter".padEnd(10)}${c.reset}`;
    const idStr = truncate(m.id, maxIdWidth).padEnd(maxIdWidth);
    const inStr = m.inputLabel.padStart(maxInWidth);
    const outStr = m.outputLabel.padStart(maxOutWidth);
    const ctxStr = fmtContext(m.contextLength).padStart(6);
    const modsStr =
      m.inMods.length || m.outMods.length
        ? `${m.inMods.join(",")} -> ${m.outMods.join(",")}`
        : "-";

    const priceColor = m.priceLabel === "Free" ? c.green : "";
    console.log(
      `  ${provTag}  ${idStr}  ${priceColor}${inStr}${c.reset}  ${priceColor}${outStr}${c.reset}  ${c.dim}${ctxStr}  ${modsStr}${c.reset}`
    );
  }

  if (limit && rows.length > limit) {
    console.log(
      `  ${c.dim}... and ${rows.length - limit} more (pass --hidden or use the "hidden" command to view all)${c.reset}`
    );
  }
}

function printReport(
  models: NormalizedModel[],
  sources: Partial<Record<ProviderId, "live" | "local">>,
  opts: {
    onlyHidden?: boolean;
    noHidden?: boolean;
    expandHidden?: boolean;
    search?: string;
    sortBy: SortField;
  }
): void {
  const filtered = sortModels(filterModels(models, opts.search), opts.sortBy);
  const visible = filtered.filter((m) => !m.hidden);
  const hidden = filtered.filter((m) => m.hidden);

  const srcSummary = Object.entries(sources)
    .map(([k, v]) => `${k}:${v}`)
    .join(", ");

  console.log("");
  console.log(
    `${c.bold}AI Model Catalog${c.reset} ${c.dim}[${srcSummary}]${c.reset}` +
      (opts.search ? ` ${c.yellow}(filter: "${opts.search}")${c.reset}` : "")
  );
  console.log(
    `${c.green}${visible.length} visible${c.reset} · ${c.gray}${hidden.length} hidden${c.reset} · ${c.dim}prices in USD per 1M tokens${c.reset}`
  );

  if (!opts.onlyHidden) {
    console.log(`\n${c.bold}${c.green}▶ Visible Models (${visible.length})${c.reset}`);
    renderTable(visible);
  }

  if (!opts.noHidden) {
    console.log(`\n${c.bold}${c.yellow}▶ Hidden Models (${hidden.length})${c.reset}`);
    const limit = opts.onlyHidden || opts.expandHidden ? undefined : 20;
    renderTable(hidden, limit);
  }
  console.log("");
}

// ---------- persistent hide / unhide ----------

function parseTarget(
  raw: string,
  defaultProvider: ProviderFilter
): { provider: ProviderFilter; id: string } {
  const match = raw.match(/^(vercel|openrouter):(.+)$/i);
  if (match) {
    return { provider: match[1].toLowerCase() as ProviderId, id: match[2].trim() };
  }
  return { provider: defaultProvider, id: raw.trim() };
}

function mutateHidden(
  action: "hide" | "unhide",
  targets: string[],
  models: NormalizedModel[],
  defaultProvider: ProviderFilter
): void {
  if (targets.length === 0) {
    console.error(`${c.red}Error:${c.reset} Please specify at least one model ID.`);
    process.exitCode = 1;
    return;
  }

  const hiddenByProvider: Record<ProviderId, Set<string>> = {
    vercel: new Set(loadJsonList(PROVIDERS.vercel.hiddenFile)),
    openrouter: new Set(loadJsonList(PROVIDERS.openrouter.hiddenFile)),
  };
  const allowedByProvider: Record<ProviderId, Set<string>> = {
    vercel: new Set(loadJsonList(PROVIDERS.vercel.allowedFile)),
    openrouter: new Set(loadJsonList(PROVIDERS.openrouter.allowedFile)),
  };
  const dirty: Record<ProviderId, boolean> = { vercel: false, openrouter: false };

  for (const rawTarget of targets) {
    const { provider, id } = parseTarget(rawTarget, defaultProvider);
    const matching = models.filter(
      (m) =>
        (provider === "all" || m.provider === provider) &&
        (m.id === id || m.slug === id)
    );

    if (matching.length === 0) {
      if (provider === "all") {
        console.warn(
          `${c.yellow}Warning:${c.reset} "${id}" was not found in either catalog. Prefix with vercel: or openrouter: to ${action} it anyway.`
        );
        continue;
      }
      // Provider was explicitly specified; apply directly even if not in current catalog.
      const set = hiddenByProvider[provider];
      if (action === "hide") {
        set.add(id);
        dirty[provider] = true;
        console.log(`${c.yellow}Hidden${c.reset} [${provider}] ${id}`);
      } else {
        const removed = set.delete(id);
        if (removed) {
          dirty[provider] = true;
          console.log(`${c.green}Unhidden${c.reset} [${provider}] ${id}`);
        } else {
          console.log(`${c.dim}Not hidden:${c.reset} [${provider}] ${id}`);
        }
      }
      continue;
    }

    for (const m of matching) {
      const set = hiddenByProvider[m.provider];
      const allowed = allowedByProvider[m.provider];
      const keys = m.slug && m.slug !== m.id ? [m.id, m.slug] : [m.id];

      if (action === "hide") {
        if (keys.some((k) => allowed.has(k))) {
          console.warn(
            `${c.yellow}Note:${c.reset} [${m.provider}] ${m.id} is in allowed_models.json (sync_models.py keeps allowlisted models visible unless removed from allowed_models.json).`
          );
        }
        for (const k of keys) set.add(k);
        dirty[m.provider] = true;
        console.log(`${c.yellow}Hidden${c.reset} [${m.provider}] ${m.id}`);
      } else {
        let removed = false;
        for (const k of keys) {
          if (set.delete(k)) removed = true;
        }
        if (removed) {
          dirty[m.provider] = true;
          console.log(`${c.green}Unhidden${c.reset} [${m.provider}] ${m.id}`);
        } else {
          console.log(`${c.dim}Already visible:${c.reset} [${m.provider}] ${m.id}`);
        }
      }
    }
  }

  for (const pid of ["vercel", "openrouter"] as ProviderId[]) {
    if (dirty[pid]) {
      saveJsonList(PROVIDERS[pid].hiddenFile, hiddenByProvider[pid]);
      console.log(`${c.dim}Saved ${PROVIDERS[pid].hiddenFile}${c.reset}`);
    }
  }
}

// ---------- interactive REPL ----------

async function runInteractive(initialProvider: ProviderFilter, localOnly: boolean): Promise<void> {
  let providerFilter: ProviderFilter = initialProvider;
  let sortBy: SortField = "id";
  let state = await loadAllModels(providerFilter, localOnly);

  const visibleCount = state.models.filter((m) => !m.hidden).length;
  const hiddenCount = state.models.length - visibleCount;
  const srcSummary = Object.entries(state.sources)
    .map(([k, v]) => `${k}:${v}`)
    .join(", ");

  console.log(
    `${c.bold}Interactive Model Browser${c.reset} ${c.dim}[${srcSummary}] — ${visibleCount} visible, ${hiddenCount} hidden${c.reset}`
  );
  console.log(
    `${c.dim}Commands: list [query] | hidden [query] | hide <id> | unhide <id> | provider <all|vercel|openrouter> | sort <id|input|output|context> | help | quit${c.reset}`
  );

  const writePrompt = () => output.write(`${c.cyan}models (${providerFilter})>${c.reset} `);
  writePrompt();

  for await (const rawLine of console) {
    const line = rawLine.trim();
    if (line) {
      const [cmd, ...rest] = line.split(/\s+/);
      const arg = rest.join(" ");

      if (cmd === "quit" || cmd === "exit" || cmd === "q") {
        break;
      } else if (cmd === "help" || cmd === "?") {
        console.log(`
  Commands:
    list [query]                 Show visible models + hidden summary
    hidden [query]               Show full Hidden Models section
    hide <id|provider:id> [...]  Persistently hide model(s)
    unhide <id|provider:id> [...] Persistently unhide model(s)
    provider <all|vercel|openrouter> Switch active provider filter
    sort <id|input|output|context>   Change sort order
    refresh                      Re-fetch catalogs from APIs / local files
    quit                         Exit interactive mode
`);
      } else if (cmd === "list" || cmd === "ls") {
        printReport(state.models, state.sources, { search: arg || undefined, sortBy });
      } else if (cmd === "hidden") {
        printReport(state.models, state.sources, {
          onlyHidden: true,
          expandHidden: true,
          search: arg || undefined,
          sortBy,
        });
      } else if (cmd === "hide" || cmd === "unhide") {
        mutateHidden(cmd, rest, state.models, providerFilter);
        state = await loadAllModels(providerFilter, true);
      } else if (cmd === "provider" || cmd === "p") {
        if (arg === "all" || arg === "vercel" || arg === "openrouter") {
          providerFilter = arg;
          state = await loadAllModels(providerFilter, localOnly);
          console.log(`Switched provider filter to ${providerFilter}.`);
        } else {
          console.log("Usage: provider <all|vercel|openrouter>");
        }
      } else if (cmd === "sort") {
        if (arg === "id" || arg === "input" || arg === "output" || arg === "context") {
          sortBy = arg;
          console.log(`Sort order set to ${sortBy}.`);
        } else {
          console.log("Usage: sort <id|input|output|context>");
        }
      } else if (cmd === "refresh") {
        state = await loadAllModels(providerFilter, false);
        console.log("Catalogs refreshed.");
      } else {
        console.log(`Unknown command "${cmd}". Type "help" for available commands.`);
      }
    }
    writePrompt();
  }
}

// ---------- CLI arg parsing ----------

function printHelp(): void {
  console.log(`
${c.bold}Usage:${c.reset}
  bun run scripts/bun/models.ts [command] [options]

${c.bold}Commands:${c.reset}
  list                        List visible models + hidden models section (default)
  hidden                      Show the full Hidden Models section with pricing
  hide <id> [id...]           Persistently hide model(s) (optional vercel: or openrouter: prefix)
  unhide <id> [id...]         Persistently unhide model(s)
  interactive                 Start interactive terminal session

${c.bold}Options:${c.reset}
  -p, --provider <name>       all | vercel | openrouter (default: all)
  -s, --search <query>        Filter models by ID, name, or provider
  --sort <field>              id | input | output | context (default: id)
  --hidden                    Expand all hidden models in the Hidden Models section
  --only-hidden               Show only the Hidden Models section
  --no-hidden                 Omit the Hidden Models section
  --local                     Read from local repo models.json without fetching live APIs
  --json                      Output normalized visible & hidden models as JSON
  -i, --interactive           Shortcut for the interactive command
  -h, --help                  Show this help message
`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const positional: string[] = [];
  let provider: ProviderFilter = "all";
  let search: string | undefined;
  let sortBy: SortField = "id";
  let expandHidden = false;
  let onlyHidden = false;
  let noHidden = false;
  let localOnly = false;
  let jsonOut = false;
  let interactive = false;

  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === "-h" || a === "--help") {
      printHelp();
      return;
    } else if (a === "-p" || a === "--provider") {
      const val = args[++i];
      if (val === "all" || val === "vercel" || val === "openrouter") {
        provider = val;
      } else {
        console.error(`Invalid provider "${val}". Expected all, vercel, or openrouter.`);
        process.exit(1);
      }
    } else if (a === "-s" || a === "--search") {
      search = args[++i];
    } else if (a === "--sort") {
      const val = args[++i];
      if (val === "id" || val === "input" || val === "output" || val === "context") {
        sortBy = val;
      } else {
        console.error(`Invalid sort field "${val}". Expected id, input, output, or context.`);
        process.exit(1);
      }
    } else if (a === "--hidden") {
      expandHidden = true;
    } else if (a === "--only-hidden") {
      onlyHidden = true;
      expandHidden = true;
    } else if (a === "--no-hidden") {
      noHidden = true;
    } else if (a === "--local") {
      localOnly = true;
    } else if (a === "--json") {
      jsonOut = true;
    } else if (a === "-i" || a === "--interactive") {
      interactive = true;
    } else if (a.startsWith("-")) {
      console.error(`Unknown option: ${a}`);
      process.exit(1);
    } else {
      positional.push(a);
    }
  }

  const command = interactive ? "interactive" : (positional[0] ?? "list");
  const rest = interactive ? positional : positional.slice(1);

  if (command === "interactive") {
    await runInteractive(provider, localOnly);
    return;
  }

  if (command === "hide" || command === "unhide") {
    const { models } = await loadAllModels(provider, localOnly);
    mutateHidden(command, rest, models, provider);
    return;
  }

  if (command !== "list" && command !== "hidden") {
    console.error(`Unknown command: ${command}`);
    printHelp();
    process.exit(1);
  }

  const { models, sources } = await loadAllModels(provider, localOnly);
  const filtered = sortModels(filterModels(models, search), sortBy);

  if (jsonOut) {
    console.log(
      JSON.stringify(
        {
          sources,
          visible: filtered.filter((m) => !m.hidden),
          hidden: filtered.filter((m) => m.hidden),
        },
        null,
        2
      )
    );
    return;
  }

  printReport(models, sources, {
    onlyHidden: onlyHidden || command === "hidden",
    noHidden,
    expandHidden: expandHidden || command === "hidden",
    search,
    sortBy,
  });
}

await main();
