# Model Check (Wails Desktop App)

A lightweight, extensible native desktop application built with **Go + Wails v2** and a zero-framework **Vanilla TypeScript + Vite** UI (no bundled Chromium, virtualized row rendering, 64 MiB Go soft memory limit).

Currently ships with **Vercel AI Gateway** support and is structured around a provider-agnostic registry so additional providers (e.g. OpenRouter, Anthropic, OpenAI) can be added without modifying the UI shell.

## Features
- **Live + offline catalog**: Fetches `https://ai-gateway.vercel.sh/v1/models` and falls back to `vercel/model-updates/models.json` when offline.
- **Persistent Hide / Hidden Models tab**: Syncs directly with `vercel/model-updates/hidden_models.json` (or `~/.config/model-check/` when run standalone outside the repo).
- **Rich model metadata**: Input/output per-1M pricing, tiered & cache pricing, context window, max output, modalities, model type filters, capability tags, ZDR/no-training status, and one-click Copy ID.
- **RAM-light design**: Native OS WebView + virtualized list (only ~30–40 DOM rows mounted at a time) + compact Go structs.

## Quick Install (Raspberry Pi OS — Debian 13 Trixie, ARM64, Wayland)

Install or update (overwrites any previously installed binary):

```bash
curl -fsSL "https://github.com/777amp/pub-info/releases/latest/download/model-check-debian13-arm64.tar.gz" | tar -xz -C /tmp && install -Dm755 /tmp/model-check ~/.local/bin/model-check && rm -f /tmp/model-check
```

Then launch on Wayland:

```bash
GDK_BACKEND=wayland model-check
```

## Prerequisites
- **Go 1.24+**
- **Bun** (or Node.js) for building the frontend bundle
- **Wails v2 CLI**: `go install github.com/wailsapp/wails/v2/cmd/wails@v2.11.0`
- **Debian 13 / Raspberry Pi OS (64-bit)**: `libgtk-3-dev` and `libwebkit2gtk-4.1-dev` (runtime: `libwebkit2gtk-4.1-0`)

## Development & Build

```bash
cd micro-apps/model-check

# Run Go unit tests (Wails-free domain layer)
go test -v ./...

# Run desktop app in dev mode with hot reload
wails dev -tags webkit2_41      # Linux (Ubuntu 24.04+)
wails dev                       # macOS / Windows

# Build native production binary
wails build -tags webkit2_41    # Linux (Ubuntu 24.04+)
wails build                     # macOS / Windows
```

## Extending with a New Provider
1. Implement [`provider.Provider`](internal/provider/provider.go) in a new package (e.g. `internal/provider/openrouter/`).
2. Register it in [`NewApp()`](app.go) via `reg.Register(...)` and optionally map its repo `hidden_models.json` path.
3. The provider automatically appears in the desktop app's provider selector.
