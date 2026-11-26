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
