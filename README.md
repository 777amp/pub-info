# pub-info

Public notes, trackers, and small automations.

## 📡 Model trackers

Each tracker pulls its catalog daily with a GitHub Action and rebuilds a `MODELS.md`.
Anything new shows up as 🆕 until you mark it seen.

### OpenRouter

<!-- OPENROUTER:START -->
<!-- OPENROUTER:END -->

### Vercel AI Gateway

<!-- VERCEL:START -->
| Listed | 🆕 Unseen | Hidden |
| :-: | :-: | :-: |
| [**518**](vercel/model-updates/MODELS.md) | **0** | **0** |

Last sync 2026-11-26 UTC · [Browse all models on Vercel AI Gateway](https://vercel.com/ai-gateway/models)
<!-- VERCEL:END -->

### Managing the lists

Run these from **Actions → (workflow) → Run workflow**:

| I want to… | Do this |
| :--- | :--- |
| Mark everything as seen | `check-openrouter` or `check-vercel` → tick `mark_seen` |
| Hide models | Same workflows, IDs in `hide`, or add them to that tracker's `hidden_models.json` |
| Always show a model | Add its ID to that tracker's `allowed_models.json` |
| Switch icons between SVG and emoji | `set-icon-mode` → pick `svg` or `emoji` |

### Layout

| Path | Purpose |
| :--- | :--- |
| `openrouter/model-updates/` | OpenRouter tracker |
| `vercel/model-updates/` | Vercel AI Gateway tracker |
| `shared/modelmd.py` | Table, icon, and README generation shared by both |
| `shared/settings.json` | Current icon style |
| `shared/icons/` | The modality SVGs, editable |

Inside each tracker folder: `MODELS.md` (generated), `allowed_models.json` (⭐ always shown),
`hidden_models.json`, `seen_models.json`, `models.json` (raw catalog), and `sync_models.py`.

## 📁 Other folders

- [`antigravity/`](antigravity) — notes and files for Antigravity

<!-- MODELS:START -->
| Listed | 🆕 Unseen | Hidden |
| :-: | :-: | :-: |
| [**38**](openrouter/model-updates/MODELS.md) | **0** | **436** |

Last sync 2026-11-26 UTC · [Browse all models on OpenRouter](https://openrouter.ai/models)
<!-- MODELS:END -->
