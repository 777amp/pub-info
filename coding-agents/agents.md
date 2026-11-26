# Coding Agents

What makes each one stand out, size (RAM/disk), providers and OAuth, extension/plugin community, and free tiers. Prices in USD unless noted. Checked 2026-11-26.

## Antigravity (Google)

Coding platform from Google where an AI agent does the work — it plans, writes the code, runs tests and checks the result, instead of just autocompleting lines as you type. Desktop app, `agy` CLI, editor extensions, Python SDK. App 2.35.2, IDE 2.8.0, CLI 1.5.18.

### What makes it stand out

- Mission-control "Manager" view: agents plan, code, test and verify; editor, terminal and browser are the agent's tools.
- Parallel agents across projects, reporting through structured Artifacts (plans, diffs, screenshots, browser recordings) you comment on like Google Docs.
- Agent-controlled browser: built-in Chrome the agent drives directly to verify what it built, using your own auth/cookies.
- Remote Agents: sessions run in Google-managed cloud and keep working after you close the laptop. Pro/Ultra only.
- Orchestrator mode: a planner model paired with a faster executor in one conversation.

### Size (RAM / disk)

| | |
|---|---|
| App download | Linux ARM64 ~196 MiB, x64 ~202 MiB; macOS ~231–240 MiB; Windows ~153–162 MiB |
| CLI `agy` binary (Linux x86_64, v1.5.18) | ~268 MB |
| Installed disk | Unverified; third-party guides say ~400–500 MB |
| RAM | No official figures. Third-party guides: 4 GB minimum, 8 GB recommended, 16 GB+ for large codebases. |

System requirements: macOS 13+, Windows 10 64-bit+, Linux glibc ≥ 2.28.

### Apps (GUI)

- Desktop app and standalone IDE (the IDE is a VS Code fork, third-party reported).

### CLI (`agy`)

- Can run on your own Gemini API key or a custom Gemini-compatible endpoint instead of Google sign-in.
- Can start Remote Agents (`agy --remote-agent`).

### Extensions / plugins

- Official editor extensions for VS Code (+Insiders), Visual Studio 2026, JetBrains, Zed, Xcode, Eclipse.
- Ecosystem is small and young: no official count, no dedicated marketplace. Known community extensions: Antigravity Usage, Brain Hub, Antigravity+, Workbench, CLI Launcher.
- No dedicated plugin SDK; extensibility is the VS Code extension API, MCP, Skills, custom agents.

### Providers and models

- No BYOK for subscription quota.
- Free: Gemini 4 Hydrogen (plus 3.8 Flash, Claude 4.6, GPT-OSS-120b until 30 Nov 2026).
- Pro/Ultra: + Gemini 4 Neon/Carbon/Argon, Claude Sonnet/Opus 5.5 (paid Pro only, not trial).
- Enterprise only: Gemini 3.7/3.6 Flash, 3.1 Pro.
- Leaving 30 Nov 2026: Gemini 4 Argon, 3.8 Flash, GPT-OSS-120b, Claude 4.6 — after that, free is Gemini-only.

### OAuth / sign-in

- Main sign-in is personal Google account OAuth, shared across App, CLI, extensions and SDK. No GitHub or other IdP sign-in.
- Secondary OAuth: GitHub repos / Drive files for Remote Agents; plugins for GitHub, Drive, Docs, Sheets, Calendar.
- Caution: routing Antigravity OAuth through third-party tools violates Google's ToS; account suspensions reported since mid-Nov 2026.

### Free tier and paid tiers

- Free $0 — weekly-refresh quota, unlimited Tab completions, Gemini 4 Hydrogen. No Remote Agents.
- Plus $4.99/mo — limited agent requests, same weekly-refresh quota bucket as Free.
- Pro $19.99/mo (CA$26.99) — quota refreshes every 5 hours until the weekly limit, all Gemini 4 models, Claude 5.5, Orchestrator, Remote Agents.
- Ultra $99.99/mo (5x Pro quota) or $199.99/mo (20x Pro) — highest quota, Gemini 4 Carbon.
- No numeric quotas published; Pro/Ultra can buy AI credits for overages.

Sources: https://antigravity.google/docs/models, https://antigravity.google/docs/plans, https://antigravity.google/docs/install, https://antigravity.google/docs/remote-agents/, https://antigravity.google/download, https://antigravity.google/pricing

## Hermes Agent (Nous Research)

Coding agent from Nous Research that runs on whichever model you point it at — OpenRouter, Anthropic, local models, whatever — all configured in one file (`~/.hermes/config.yaml`). Open source (MIT), Python. v0.23.4 (23 Nov 2026). Repo: NousResearch/hermes-agent — 266,225 stars / 60,395 forks (Nov 2026). Don't install from PyPI (stale at 0.19.0); use the official installer.

### What makes it stand out

- Self-improving learning loop: creates skills from experience, searches past conversations, builds a user model across sessions.
- Config tiers in `~/.hermes/config.yaml`: primary model, up to 9 auxiliary slots, delegation (subagents), compression, fallback provider chains, isolated profiles.
- Fallback provider chains: tries providers entry-by-entry when the primary fails; swaps model + provider mid-session without losing the conversation.
- Messaging gateway: one background process speaks 20+ chat platforms (Telegram, Discord, Slack, WhatsApp, Signal, SMS, Email, Matrix, Teams, LINE, …) with cross-platform conversation continuity.
- Built-in cron: natural-language schedules (daily reports, nightly backups) delivered to any platform.
- 7 execution backends: local, Docker, SSH, Modal, Daytona, Vercel Sandbox, Singularity via plugin; Modal/Daytona hibernate when idle.
- Subagents + Kanban: isolated subagents for parallel workstreams, shared Kanban board.

### Size (RAM / disk)

| | |
|---|---|
| Minimum (official Docker guide) | 1 GB RAM, 1 CPU core, 500 MB disk |
| Recommended | 2–4 GB RAM, 2 cores, 2+ GB disk (grows with sessions and skills) |
| At rest | ~250 MiB RSS; gateway ~223–259 MiB whole-server |
| Install footprint | Installer path ~2.5 GB disk (3.0 GB after one update); install peaks at ~1.3 GB RAM, so plan 2 GB RAM for the installing box. Docker image ~900 MB compressed. |
| Platforms | 64-bit Linux (x86_64 + ARM/aarch64), macOS, Windows 10/11, WSL2, Docker, Termux (aarch64) |

### Apps (GUI)

- Hermes Desktop (Electron) and a web dashboard.

### CLI (`hermes`)

- Config in `~/.hermes/config.yaml`; keys in `~/.hermes/.env`, never in the config.
- Ships a local OpenAI-compatible API server (`127.0.0.1:8642`) and an ACP server for editors.

### Extensions / plugins

- `hermes plugins install <name>` (official catalog) or `owner/repo` (any Git repo). Plugins are Python packages; installs land disabled by default.
- No official plugin count; a Sep 2026 catalog validation reported 299 valid plugin files.
- Notable: `whatsapp-agent-platform` (≥ 0.21.4), `browserless`, `github-copilot` (labs plugin), `comemo`, `go-whatsapp`.
- Built-in MCP client; tools surface as `mcp__<server>__<tool>`.
- Skills: built-in library, autonomous skill creation, compatible with the agentskills.io open standard.

### Providers and models

- 40+ named providers — OpenRouter, Anthropic, OpenAI Codex, Google Gemini/Vertex, Azure, AWS Bedrock, NVIDIA NIM, Vercel AI Gateway, DeepSeek, xAI, DashScope, Kilo Code, Hugging Face, Ollama, LM Studio, Muse Spark, GitHub Copilot (labs plugin) — plus any OpenAI-compatible endpoint and local Ollama/vLLM/llama.cpp.
- Own models: Hermes 3 / Hermes 4 open-weight, built for agentic workloads.
- Nous Portal is the recommended route: one OAuth login, 300+ models (351 listed Nov 2026), plus a Tool Gateway (web search, image gen, TTS, browser automation).
- Models need a large context: docs say serve at least a 64K window on local endpoints.

### OAuth / sign-in

- No central sign-in: no Google or GitHub login for Hermes itself; each provider authenticates its own way.
- Nous Portal — OAuth, the recommended single sign-in.
- ChatGPT / Codex — device-code OAuth, or browser PKCE on `localhost:1455`.
- Claude Max — OAuth, but only Max + purchased extra credits (Pro can't use it, use an API key).
- OpenRouter — browser PKCE (`hermes auth add openrouter --type oauth`).
- Google Vertex AI — OAuth2 via service account or ADC. Gemini consumer plans (AI Pro/Ultra) have no sign-in path — API key only.
- GitHub Copilot — device-code login via the `github-copilot` labs plugin.
- Multiple logins can coexist in an auth pool (`~/.hermes/auth.json`).

### Free tier and paid tiers

- Software is free, MIT, no feature gates. You pay only for LLM usage. No per-seat or Pro version.
- Nous Portal (optional):
  - Free $0 — free models only (four `:free` models, Nov 2026), standard rate limits, $0 monthly credits.
  - Plus $20/mo — $22 credits, $10 rollover cap. Includes agent usage within limits, Tool Gateway, one hosted Cloud agent.
  - Super $100/mo — $110 credits, $50 cap.
  - Ultra $200/mo — $220 credits, $100 cap.
- Top-ups $10–$200 via Stripe. Hermes Cloud (hosted always-on agent, cron 24/7) included with paid plans, billed daily from credits in arrears.

Sources: https://github.com/NousResearch/hermes-agent, https://hermes-agent.nousresearch.com/docs/integrations/providers, https://portal.nousresearch.com/manage-subscription, https://playnhost.com/knowledgebase/hermes-agent-hosting/how-much-memory-does-hermes-agent-need/, https://heyhermes.app/guides/hermes-agent-hardware-requirements

## Pi (Earendil)

Terminal coding agent with a tiny core — four built-in tools (`read`, `write`, `edit`, `bash`) and a system prompt under 1,000 tokens; everything else is opt-in via extensions. Now Earendil Inc. (was badlogic/pi-mono); npm `@earendil-works/pi-coding-agent` v1.6.1 (old `@mariozechner` scope is deprecated). Repo: earendil-works/pi — 123,994 stars / 16,026 forks (Nov 2026), MIT.

### What makes it stand out

- Minimal core by design: four built-in tools only; sub-agents, plan mode and permission prompts deliberately not built in — add them via extensions.
- Mid-session model switching: `/model` (fuzzy search) or Ctrl+L; Ctrl+P cycles favorite models.
- Native MCP since 1.0, plus Codemode: a QuickJS sandbox where the model writes short JavaScript to call, filter and parallelize MCP tools without dumping schemas into context.
- Pi Durable (experimental): checkpoints every turn, tool call and compaction to SQLite, JSONL or Cloudflare Durable Objects — crash-safe, always-on background agents.
- No permission prompts: runs with your account's permissions and never asks before a tool call — sandbox it yourself (Docker, Gondolin micro-VM extension, OpenShell sandbox).

### Size (RAM / disk)

| | |
|---|---|
| npm package unpacked (v1.6.1) | ~23.8 MiB, 1,330 files |
| Full installed footprint | Unverified (deps include pi-ai, pi-mcp, pi-tui, pi-codemode, pi-agent-core, photon-node) |
| RAM (measured) | ~144 MB per active session; ~76 MB extra per added session; 833 MB for 10 sessions |
| Runtime | TypeScript on Node.js; requires Node >= 22.19.0 |

### Apps (GUI)

- Pi itself is terminal-only. Third-party GUIs: Pi GPUI (Rust native, ~16 MB download, ~75 MB idle measured); Electron clients (190–430 MB idle measured).

### CLI (`pi`)

- Install: official installer (`curl -fsSL https://pi.dev/install.sh | sh`, pins deps, updates via `pi update`), npm, Nix, Windows PowerShell.
- Four ways to run: interactive fullscreen TUI, print/JSON mode for scripts, RPC over stdin/stdout, TypeScript SDK.

### Extensions / plugins

- Extensions are TypeScript modules running in-process: tools, commands, shortcuts, event handlers, UI, RAG, memory, sub-agent spawning, permission gates, MCP, custom editors.
- Install: `pi install npm:<package>` (or from git); `pi list`, `pi update`. Extensions, skills, prompt templates and themes bundle into shareable Pi packages via npm or git.
- Skills: Agent Skills spec (`SKILL.md`), lazy-loaded only when needed.
- MCP: built in since 1.0 — `pi mcp add <name> --url …`, config in `~/.pi/agent/mcp.json`.
- Ecosystem: ~5,700 packages at pi.dev/packages. Notable: `safe-git`, `pi-cost-dashboard`, `pi-notify`, `checkpoint`, `wj-pi-subagents`, `pi-web-search-lite`, `@bachi/pi-coder`.
- pi.dev's own warning: packages can execute code and influence agent behavior — review the source before installing third-party packages.

### Providers and models

- 15+ built-in providers, hundreds of models (tool-capable models only; catalog refreshes from pi.dev at runtime).
- Subscriptions via `/login`: Claude Pro/Max, ChatGPT Plus/Pro (Codex), GitHub Copilot, Google Gemini CLI, Google Antigravity (free with a Google account). Docs no longer publish the full list — confirm in the CLI.
- API keys: Anthropic, OpenAI, Azure, Gemini, Vertex, Bedrock, Mistral, Groq, Cerebras, xAI, OpenRouter, Vercel AI Gateway, DeepSeek, NVIDIA, Cloudflare, Hugging Face, Kimi, MiniMax, ZAI, OpenCode Zen/Go.
- Custom providers in `~/.pi/agent/models.json`: any OpenAI/Anthropic/Google-compatible endpoint — Ollama, LM Studio, vLLM, SGLang, proxies, Vercel AI Gateway. Local models via `/llama` (llama.cpp router, GGUF on demand).

### OAuth / sign-in

- `/login` is the OAuth entry point; credentials stored in `auth.json` (`/logout` removes them). No Google/GitHub sign-in for Pi itself; OAuth is per provider.
- Claude Pro/Max OAuth — note: third-party harness usage draws from Anthropic extra usage, billed per token, not the plan allowance.
- OAuth via provider extensions too (e.g. Mistral, SenseTime Raccoon).
- API keys via env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …) or stored through `/login`. Precedence: `--api-key` flag, then `auth.json`, then `models.json`, then env vars.

### Free tier and paid tiers

- Software is free, MIT, $0 — no plan, no seat price, no hosted service. Every dollar is model tokens, paid to whichever provider/subscription you configure.
- No free models from Pi itself — free only via providers (Gemini CLI / Antigravity free tiers with a Google account).
- Radius (Earendil's own gateway, optional, early alpha): prepaid credits at providers' list prices; no public price list.
- MIT stays MIT, per Earendil — some future value-add features will be source-available then open source after a delay, some enterprise features proprietary. No paid edition of the harness exists today.

Sources: https://github.com/earendil-works/pi, https://registry.npmjs.org/@earendil-works/pi-coding-agent/latest, https://www.eesel.ai/blog/pi-coding-agent, https://pi.dev/packages
