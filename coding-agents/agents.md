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
