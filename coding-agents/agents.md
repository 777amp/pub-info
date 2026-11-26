# Coding Agents

What makes each one stand out, size (RAM/disk), providers and OAuth, extension/plugin community, and free tiers. Prices in USD unless noted. Checked 2026-11-26.

## Antigravity (Google)

Agent-first coding platform from Google: desktop app, `agy` CLI, editor extensions, Python SDK, one agent runtime. App 2.35.2, IDE 2.8.0, CLI 1.5.18. Launched 18 Nov 2025; rebuilt as 2.0 at Google I/O, 19 May 2026.

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

### Providers and models

- No BYOK for subscription quota.
- Gemini 4 Neon/Carbon/Argon/Hydrogen, Gemini 3.8 Flash, Claude Sonnet/Opus 5.5 (Pro paid non-trial only, Ultra, Enterprise), Claude 4.6, GPT-OSS-120b.
- Leaving 30 Nov 2026: Gemini 4 Argon, 3.8 Flash, GPT-OSS-120b, Claude 4.6 — after that free is effectively Gemini-only (Hydrogen).
- CLI exception: `agy` can run on your own Gemini API key or a custom Gemini-compatible endpoint.

### OAuth / sign-in

- Main sign-in is personal Google account OAuth, shared across App, CLI, extensions and SDK. No GitHub or other IdP sign-in.
- Business: Google Cloud SSO, Workforce Identity Federation / BYOID, or ADC on your own GCP project.
- Secondary OAuth: GitHub repos / Drive files for Remote Agents; plugins for GitHub, Drive, Docs, Sheets, Calendar.
- Caution: routing Antigravity OAuth through third-party tools violates Google's ToS; account suspensions reported since mid-Nov 2026.

### Extensions / plugins

- Official extensions for VS Code (+Insiders), Visual Studio 2026, JetBrains, Zed, Xcode, Eclipse; plus the standalone IDE (a VS Code fork, third-party reported).
- Ecosystem is small and young: no official count, no dedicated marketplace. Known community extensions: Antigravity Usage, Brain Hub, Antigravity+, Workbench, CLI Launcher.
- No dedicated plugin SDK; extensibility is the VS Code extension API, MCP, Skills, custom agents.

### Free tier and paid tiers

| Plan | Price (USD) | Notes |
|---|---|---|
| Individual (free) | $0/mo | Weekly-refresh quota; unlimited Tab completions; Gemini 4 Hydrogen (plus 3.8 Flash, Claude 4.6, GPT-OSS-120b until 30 Nov 2026). No Remote Agents. |
| Google AI Plus | $4.99/mo | Limited agent requests; same weekly-refresh quota bucket as Free. |
| Google AI Pro | $19.99/mo | Quota refreshed every 5 hours until weekly limit; Gemini 4 Neon/Carbon/Argon/Hydrogen; Claude 5.5 (paid non-trial only); Orchestrator; Remote Agents. CA$26.99/mo in Canada. |
| Google AI Ultra | $99.99/mo (5x Pro) or $199.99/mo (20x Pro) | Highest quota; Gemini 4 Carbon. |
| Business (Gemini Enterprise) | From $30/seat/mo or pay-as-you-go | Enterprise models only; no Remote Agents or voice mode. |

- Google publishes no numeric quota for any plan.
- Pro/Ultra can buy AI credits for over-quota usage.

Sources: https://antigravity.google/docs/models, https://antigravity.google/docs/plans, https://antigravity.google/docs/install, https://antigravity.google/docs/remote-agents/, https://antigravity.google/download, https://antigravity.google/pricing

## Hermes Agent (Nous Research)

Multi-model agent runtime from Nous Research. Open source (MIT), Python; installer bundles Python 3.14, Node.js, pnpm, ripgrep, FFmpeg. v0.23.4 (23 Nov 2026). Repo: NousResearch/hermes-agent — 266,225 stars / 60,395 forks (Nov 2026). Don't install from PyPI (stale at 0.19.0); use the official installer.

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

### Providers and models

- 40+ named providers: Nous Portal, OpenAI Codex, Anthropic, OpenRouter, Vercel AI Gateway, DeepSeek, Google Gemini, Vertex AI, Azure, AWS Bedrock, NVIDIA NIM, xAI, DashScope, Kilo Code, Hugging Face, Ollama, LM Studio, Muse Spark, GitHub Copilot (labs plugin) — plus any OpenAI-compatible endpoint and local Ollama/vLLM/llama.cpp.
- Own models: Hermes 3 / Hermes 4 open-weight, built for agentic workloads; the runtime works with any OpenAI-compatible endpoint.
- Nous Portal is the recommended route: one OAuth login, 300+ models (351 listed Nov 2026), plus a Tool Gateway (web search, image gen, TTS, browser automation).
- Models need a large context: docs say serve at least a 64K window on local endpoints.

### OAuth / sign-in

- No central sign-in: no Google or GitHub login for Hermes itself; each provider authenticates its own way.
- Nous Portal — OAuth, the recommended single sign-in.
- ChatGPT / Codex — device-code OAuth, or browser PKCE on `localhost:1455`.
- Claude Max — OAuth, but only Max + purchased extra credits (Claude Pro can't use the OAuth path, use an API key).
- OpenRouter — `hermes auth add openrouter --type oauth` (browser PKCE).
- Google Vertex AI — OAuth2 via service account or ADC. Gemini consumer plans (AI Pro/Ultra) have no sign-in path — API key only.
- GitHub Copilot — device-code login via the `github-copilot` labs plugin.

### Extensions / plugins

- `hermes plugins install <name>` (official catalog) or `owner/repo` (any Git repo). Plugins are Python packages; installs land disabled by default.
- No official plugin count; a Sep 2026 catalog validation reported 299 valid plugin files.
- Notable: `whatsapp-agent-platform` (≥ 0.21.4), `browserless`, `github-copilot` (labs plugin), `comemo`, `go-whatsapp`.
- Built-in MCP client; tools surface as `mcp__<server>__<tool>`.
- Skills: built-in library, autonomous skill creation, compatible with the agentskills.io open standard.

### Free tier and paid tiers

- Software is free, MIT, no feature gates. You pay only for LLM usage. No per-seat or Pro version.
- Nous Portal (optional):

| Plan | Price (USD) | Notes |
|---|---|---|
| Free | $0 | Free models only, standard rate limits, $0 monthly credits. |
| Plus | $20/mo | $22 credits, $10 rollover cap. Includes agent usage within limits, Tool Gateway, one hosted Cloud agent. |
| Super | $100/mo | $110 credits, $50 cap. |
| Ultra | $200/mo | $220 credits, $100 cap. |

- Four `:free` models on Portal (Nov 2026), usable indefinitely on Free. Top-ups $10–$200 via Stripe.
- Hermes Cloud (hosted always-on agent, cron 24/7) included with paid Portal plans, billed daily from credits in arrears.

Sources: https://github.com/NousResearch/hermes-agent, https://hermes-agent.nousresearch.com/docs/integrations/providers, https://portal.nousresearch.com/manage-subscription, https://playnhost.com/knowledgebase/hermes-agent-hosting/how-much-memory-does-hermes-agent-need/, https://heyhermes.app/guides/hermes-agent-hardware-requirements
