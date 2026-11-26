# pub-info

Public notes, trackers, and small automations.

## 📡 Model trackers

Each tracker pulls its catalog daily with a GitHub Action and rebuilds its
`MODELS.md`.

Automatic syncs display newly discovered models with a pending-review icon.
Models in `allowed_models.json` are starred and always remain visible.

### OpenRouter

<!-- OPENROUTER:START -->
| Listed | 🕒 Pending review | Hidden |
| :-: | :-: | :-: |
| [**46**](openrouter/model-updates/MODELS.md) | **27** | **428** |

Last sync 2026-11-26 UTC · [Browse all models on OpenRouter](https://openrouter.ai/models)
<!-- OPENROUTER:END -->

### Vercel AI Gateway

<!-- VERCEL:START -->
| Listed | 🕒 Pending review | Hidden |
| :-: | :-: | :-: |
| [**518**](vercel/model-updates/MODELS.md) | **0** | **0** |

Last sync 2026-11-26 UTC · [Browse all models on Vercel AI Gateway](https://vercel.com/ai-gateway/models)
<!-- VERCEL:END -->

### Managing the lists

Run these from **Actions → (workflow) → Run workflow**:

| I want to… | Do this |
| :--- | :--- |
| Review the catalog | Manually run the relevant workflow |
| Approve models | Add their IDs to that tracker's `allowed_models.json` |
| Hide everything not approved | Manually run the workflow after updating the allow-list |
| Hide specific models manually | Supply their IDs in the workflow's `hide` input |
| Switch icons between SVG and emoji | `set-icon-mode` → pick `svg` or `emoji` |

### How model review works

- ⭐ **Allowlisted:** always visible and starred.
- 🕒 **Pending review:** visible during automatic syncs, but not yet allowlisted.
- **Hidden:** models not allowlisted after a manual workflow run.
- Adding a hidden model to the allow-list makes it visible again.
- Automatic syncs never hide newly discovered models.

### Layout

| Path | Purpose |
| :--- | :--- |
| `openrouter/model-updates/` | OpenRouter tracker |
| `vercel/model-updates/` | Vercel AI Gateway tracker |
| `shared/modelmd.py` | Shared table, icon, and README generation |
| `shared/settings.json` | Current icon style |
| `shared/icons/` | Shared SVG icons |

Inside each tracker folder: `MODELS.md`, `allowed_models.json`,
`hidden_models.json`, `seen_models.json`, `models.json`, and `sync_models.py`.

## 📁 Other folders

- [`antigravity/`](antigravity) — notes and files for Antigravity