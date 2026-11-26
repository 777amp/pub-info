# Coding Agents

Notes on coding agents: what makes each one stand out, size (RAM/disk), providers and OAuth, extension/plugin community, and free tiers. Prices in USD unless noted. Checked 2026-11-26.

## Antigravity (Google)

Agent-first coding platform from Google. One agent runtime across four surfaces: desktop app, `agy` CLI, editor extensions, and a Python SDK. Versions in force 2026-11-26: App 2.35.2, standalone IDE 2.8.0, CLI 1.5.18. Launched 18 Nov 2025; rebuilt as 2.0 at Google I/O, 19 May 2026.

### What makes it stand out

- Agent-first, not autocomplete-first: a mission-control "Manager" view where agents plan, code, test and verify; the editor, terminal and browser are tools the agent uses.
- Parallel agents across workspaces/projects, reporting through structured Artifacts (plans, diffs, screenshots, browser recordings) you comment on Google-Docs-style.
- Agent-controlled browser: a built-in Chrome/Chromium the agent drives directly (click, fill forms, run JS, screenshots, recordings) to verify what it built, using your own auth/cookies.
- Remote Agents: sessions run in an isolated Google-managed cloud environment and keep working after you close the laptop; startable from the App, CLI (`agy --remote-agent`) or antigravity.google.com. Pro/Ultra only.
- Orchestrator mode: a planner model (Gemini 4 Neon/Carbon/Argon or Claude Opus 5.5) paired with a faster executor (Gemini 4 Hydrogen or Claude Sonnet 5.5) in one conversation.
- Multi-agent primitives: subagents, Swarm, Boost (manager-worker hierarchy), Teamwork (`/teamwork-preview`), scheduled tasks/automations, voice mode (Gemini Live).
- Steering: MCP servers, Agent Skills (SKILL.md), custom agents, rules (GEMINI.md), execution policies/sandboxing.

### Size (RAM / disk)

| | |
|---|---|
| App download (Linux ARM64 .tar.gz) | ~196 MiB |
| App download (Linux x64 .tar.gz) | ~202 MiB |
| App download (macOS Apple Silicon / Intel .dmg) | ~231 / ~240 MiB |
| App download (Windows ARM64 / x64 .exe) | ~153 / ~162 MiB |
| CLI `agy` binary (Linux x86_64, v1.5.18) | ~268 MB |
| Installed disk footprint | Unverified; third-party guides say ~400–500 MB / 500 MB free space |
| RAM | No official idle/load figures. Third-party guides citing official requirements: 4 GB minimum, 8 GB recommended, 16 GB+ for large codebases. Reported: 1 GB+ idle, spikes to ~5 GB on big projects (unverified, incl. a reported memory leak in a monorepo). |

System requirements: macOS 13 Ventura+, Windows 10 64-bit+, Linux glibc ≥ 2.28.

### Providers and models

- No BYOK for subscription quota: "There is currently no support for Bring-your-own-key (BYOK) or bring-your-own-endpoint for additional rate limits."
- Models (selector under the prompt box; thinking Low / Medium / High, plus Extra on Gemini 4 Neon/Hydrogen):
  - Gemini 4 Neon / Carbon / Argon / Hydrogen; Gemini 3.8 Flash; Gemini 3.7 / 3.6 Flash, 3.1 Pro (Enterprise only)
  - Claude Sonnet 5.5 / Opus 5.5 (thinking) — Pro (paid non-trial only), Ultra, Enterprise
  - Claude Sonnet / Opus 4.6, GPT-OSS-120b — leaving 30 Nov 2026, along with Gemini 4 Argon and 3.8 Flash. After that the free tier is effectively Gemini-only (Hydrogen).
- CLI exception: `agy` can run on your own Gemini API key (`GEMINI_API_KEY`) or a custom Gemini-compatible endpoint (`GOOGLE_GEMINI_BASE_URL`) instead of Google sign-in.
- Python SDK only: local models via Ollama / LM Studio / vLLM (not in the App/IDE).

### OAuth / sign-in

- Main sign-in is personal Google account OAuth (browser flow), shared across App, CLI, IDE extensions and SDK on the same machine. No GitHub or other IdP sign-in for the main account.
- Business: Google Cloud SSO, Workforce Identity Federation / BYOID (e.g. Okta), or Application Default Credentials; Gemini Enterprise seat or pay-as-you-go (own GCP project, per-token billing).
- Headless/SSH: CLI prints an authorization URL + code to paste back.
- Secondary OAuth: Remote Agents attach GitHub repos / Google Drive files via OAuth; plugins for GitHub, Drive, Docs, Sheets, Slides, Calendar connect via OAuth.
- Caution: routing Antigravity OAuth through third-party tools violates Google's ToS; account suspensions reported since mid-Nov 2026.

### Extensions / plugins

- Official editor extensions: VS Code and VS Code Insiders (`Google.google-antigravity`), Visual Studio 2026, JetBrains IDEs, Zed, Xcode, Eclipse (some Enterprise in Preview). Plus the standalone Antigravity IDE.
- The standalone IDE is a VS Code fork (third-party reported, not officially confirmed); full Open VSX registry compatibility is claimed by third parties, not confirmed by Google.
- Ecosystem is small and young: no official extension count or dedicated marketplace. Known community extensions: Antigravity Usage (token/quota tracker), Brain Hub for Antigravity, Antigravity+ (auto-accept, quota monitor), Antigravity Workbench (multi-account manager), Antigravity CLI Launcher.
- No dedicated Antigravity plugin SDK; extensibility is the VS Code extension API, MCP servers, Agent Skills, custom agents and slash commands. Python SDK (`google-antigravity`, Python 3.10+) is the programmatic surface.

### Free tier and paid tiers

| Plan | Price (USD) | Notes |
|---|---|---|
| Individual (free) | $0/mo | Weekly-refresh quota; unlimited Tab completions + Command requests; all product features incl. scheduled tasks and CLI; Gemini 4 Hydrogen (plus 3.8 Flash, Claude 4.6, GPT-OSS-120b until 30 Nov 2026). No Remote Agents. |
| Google AI Plus | $4.99/mo | Limited agent requests; same weekly-refresh quota bucket as Free. |
| Google AI Pro | $19.99/mo | High quota refreshed every 5 hours until the weekly limit; Gemini 4 Neon/Carbon/Argon/Hydrogen; Claude Sonnet/Opus 5.5 (paid non-trial only); Orchestrator; Remote Agents (personal account only). CA$26.99/mo in Canada. |
| Google AI Ultra | $99.99/mo (5x Pro quota) or $199.99/mo (20x Pro quota) | Highest quota, refreshed every 5 hours; Gemini 4 Carbon; third-party models. |
| Business (Gemini Enterprise) | From $30/seat/mo or pay-as-you-go | Via Google Cloud; enterprise models only; Remote Agents and voice mode NOT available on business accounts. |

- Google publishes no numeric quota (no request/token counts) for any plan; limits depend on capacity and task complexity.
- Pro/Ultra can buy AI credits for over-quota usage (Gemini Enterprise consumption prices; "AI Credit Overages" Never / Always). Credit pack prices shown only after sign-in.
- Stale price warning: pages quoting Ultra at $249.99/mo are outdated; Google replaced it with the $99.99/$199.99 split at I/O in May 2026.

Sources: https://antigravity.google/docs/models, https://antigravity.google/docs/plans, https://antigravity.google/docs/install, https://antigravity.google/docs/remote-agents/, https://antigravity.google/download, https://antigravity.google/pricing

## Hermes Agent (Nous Research)

Multi-model agent runtime from Nous Research. Open source (MIT), Python; the installer bundles Python 3.14, Node.js, pnpm, ripgrep and FFmpeg. Version in force 2026-11-26: v0.23.4 (released 23 Nov 2026). Repo: NousResearch/hermes-agent — 266,225 stars / 60,395 forks (GitHub, Nov 2026). Do not install from PyPI (stale at 0.19.0, Jul 2026); use the official installer.

### What makes it stand out

- Self-improving learning loop: it creates skills from experience, improves them during use, searches past conversations (FTS5 + LLM summarization) and builds a user model across sessions.
- Multi-model runtime with config tiers: `model:` (primary) plus `auxiliary.*` (compression, title, vision, web extract, session search, skills hub, approval, MCP, curator — up to 9 slots), `delegation.*` (subagent model/limits), `compression.*`, `fallback_providers:` chains, `profiles:` (fully isolated `HERMES_HOME` dirs) — all in `~/.hermes/config.yaml`.
- Fallback provider chains: `fallback_providers:` tried entry-by-entry when the primary fails (rate limits, server errors, auth failures); swaps model + provider mid-session without losing the conversation.
- Messaging gateway: one background gateway process speaks 20+ chat platforms — Telegram, Discord, Slack, WhatsApp, Signal, SMS, Email, Home Assistant, Mattermost, Matrix, DingTalk, Feishu/Lark, WeCom, Weixin, BlueBubbles (iMessage), QQ, Teams, LINE, ntfy — with voice-memo transcription and cross-platform conversation continuity.
- Built-in cron / scheduled automations: natural-language schedules (daily reports, nightly backups, weekly audits) delivered to any platform, running unattended.
- Runs anywhere: 7 execution backends — local, Docker (read-only rootfs, dropped capabilities, namespace isolation), SSH, Modal, Daytona, Vercel Sandbox, Singularity via plugin; Modal/Daytona hibernate when idle and wake on demand.
- Subagents + Kanban: isolated subagents for parallel workstreams (max 3 concurrent children, depth configurable to 3), a shared Kanban board (`hermes kanban`), and Python scripts that call tools via RPC.
- Also ships a local OpenAI-compatible API server (`127.0.0.1:8642`), an ACP server for editors, an MCP server, a web dashboard, and Hermes Desktop (Electron).

### Size (RAM / disk)

| | |
|---|---|
| Minimum (official Docker guide) | 1 GB RAM, 1 CPU core, 500 MB disk |
| Recommended (official Docker guide) | 2–4 GB RAM, 2 cores, 2+ GB disk (grows with sessions and skills) |
| Measured at rest | ~250 MiB RSS for the agent process; gateway ~223–259 MiB whole-server |
| Measured fleet (31 containers) | Median 282 MB RSS, max 858 MB; peak 1.1 GB mid-response |
| Install footprint | Installer path ~2.5 GB disk (3.0 GB after one update); install itself peaks at ~1.3 GB RAM, so plan on 2 GB RAM for a box where Hermes installs/updates itself. Official Docker image ~900 MB compressed. Base install "under 500 MB" per one guide (installer-fetched packages account for the rest). |
| Platforms | 64-bit Linux (x86_64 + ARM/aarch64), macOS, Windows 10/11 native, WSL2, Docker, Termux (signed APT repo, aarch64) |

### Providers and models

- 40+ named providers in the official docs: Nous Portal, OpenAI Codex, Anthropic, OpenRouter, Vercel AI Gateway, z.ai/GLM, Kimi/Moonshot, DeepSeek, Google Gemini, Vertex AI, OpenAI API, Azure AI Foundry, AWS Bedrock, NVIDIA NIM, xAI, Alibaba/DashScope, Kilo Code, Hugging Face, Ollama Cloud, StepFun, LM Studio, Meta Model API (Muse Spark), GitHub Copilot (labs plugin) — plus any custom OpenAI-compatible endpoint and local Ollama/vLLM/llama.cpp.
- Own models: Hermes 3 / Hermes 4 open-weight models from Nous Research, purpose-built for agentic workloads; the runtime is separate from the models and can use any OpenAI-compatible endpoint.
- Nous Portal is the recommended route: one OAuth login covers 300+ frontier models (351 listed Nov 2026) plus a Tool Gateway (web search, image gen, TTS, browser automation). `hermes setup --portal`.
- Model requirement: models need a large context — docs say serve at least a 64K window on local endpoints.
- Auth: keys live in `~/.hermes/.env`, never in `config.yaml`. Credentials kept in a pool (`~/.hermes/auth.json`); multiple logins can coexist.

### OAuth / sign-in

- No central sign-in: no Google account sign-in and no GitHub IdP login for Hermes itself; each provider authenticates its own way.
- OAuth logins that exist, per provider:
  - Nous Portal — OAuth, the recommended single sign-in.
  - ChatGPT / OpenAI Codex — device-code OAuth by default, or browser PKCE on `localhost:1455`; can import Codex CLI credentials from `~/.codex/auth.json`.
  - Anthropic — Claude Max OAuth, but only Max + purchased extra usage credits (base Max allowance is never consumed; Claude Pro cannot use the OAuth path — use an API key).
  - xAI SuperGrok / X Premium+ — browser OAuth, uses subscription quota.
  - OpenRouter — `hermes auth add openrouter --type oauth` (browser PKCE flow).
  - Qwen, MiniMax — browser PKCE logins.
  - Google Vertex AI — OAuth2 via service-account JSON or ADC (GCP billing). Google Gemini consumer plans (AI Pro/Ultra) have no sign-in path — the `gemini` provider is API-key only.
  - GitHub Copilot — device-code login via the `github-copilot` labs plugin.
  - MCP servers — OAuth supported (`hermes mcp add … --auth oauth`, `hermes mcp login <server>`).

### Extensions / plugins

- Plugin system: `hermes plugins install <name>` (official catalog) or `hermes plugins install owner/repo` (any Git repo); list/enable/disable/update/remove/config. Plugins are Python packages; catalog entries are reviewed/pinned. Installs land disabled by default.
- Ecosystem size: no official count published; a catalog validation run in Sep 2026 reported 299 valid plugin-catalog files.
- Notable plugins: `whatsapp-agent-platform` (Meta's WhatsApp Agent Platform API, requires Hermes ≥ 0.21.4, key `WHATSAPP_AGENT_PLATFORM_API_KEY`), `browserless` (browser tools on Browserless cloud browsers, ≥ 0.21.6), `youdotcom-oss/agent-skills` (You.com search/research/finance MCP + skills), `comemo` (composite memory: Honcho + Mem0 + Supermemory), `go-whatsapp` (GOWA server, ≥ 0.23.1), `github-copilot` (labs plugin by Nous), `stalkchain`, `automem`.
- MCP: built-in MCP client (`hermes mcp add/list/test/login`, `mcp_servers` in `config.yaml`); tools surface as `mcp__<server>__<tool>`.
- Skills: built-in skill library (`hermes skills list/install`); autonomous skill creation and self-improvement; compatible with the agentskills.io open standard (portable to 11+ other tools).

### Free tier and paid tiers

- The software is free, MIT-licensed, with no feature gates. You pay only for the LLM usage from whichever provider you point it at. There is no per-seat or Pro version of Hermes Agent.
- Nous Portal (optional, recommended paid route):

| Plan | Price (USD) | Notes |
|---|---|---|
| Free | $0 | Free models only, standard rate limits, $0 monthly credits. |
| Plus | $20/mo | $22 credits, $10 rollover cap. Includes Hermes Agent usage within daily/weekly/monthly limits, Tool Gateway, one hosted Cloud agent (4 GB RAM / 25 GB disk). |
| Super | $100/mo | $110 credits, $50 cap. Cloud agent 4 GB / 100 GB. |
| Ultra | $200/mo | $220 credits, $100 cap. Cloud agent 8 GB / 100 GB. |

- Top-ups $10–$200 via Stripe. API-key usage always burns credits pay-as-you-go, not included usage.
- Free models on Portal: four `:free` models (Nov 2026), usable indefinitely on the Free plan; plus a one-time free trial model (`nous/welcome`, setup chat only, once per OS user).
- Hermes Cloud (hosted always-on agent, cron 24/7) is included with paid Portal plans and billed daily from credits in arrears. Portal also accepts an eligible ChatGPT plan for inference with no Nous subscription (tools/hosting billed separately).

Sources: https://github.com/NousResearch/hermes-agent, https://hermes-agent.nousresearch.com/docs/integrations/providers, https://portal.nousresearch.com/manage-subscription, https://playnhost.com/knowledgebase/hermes-agent-hosting/how-much-memory-does-hermes-agent-need/, https://heyhermes.app/guides/hermes-agent-hardware-requirements
