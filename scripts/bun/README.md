# Bun Scripts

Zero-dependency [Bun](https://bun.sh) scripts for working with `pub-info` catalogs.

## `models.ts`

Displays models and per-1M-token pricing from **Vercel AI Gateway** and **OpenRouter**, with persistent model hiding synced directly with:

- `vercel/model-updates/hidden_models.json`
- `openrouter/model-updates/hidden_models.json`

Fetches live data from both APIs by default and automatically falls back to the repo's local `models.json` snapshots (or pass `--local` to skip network requests).

### Usage

```bash
# List visible models + Hidden Models section
bun run scripts/bun/models.ts

# Filter by provider, search term, or sort by price/context
bun run scripts/bun/models.ts --provider vercel --sort input
bun run scripts/bun/models.ts --provider openrouter --search claude --sort output

# View the full Hidden Models section
bun run scripts/bun/models.ts hidden

# Persistently hide or unhide models (optional vercel: / openrouter: prefix)
bun run scripts/bun/models.ts hide vercel:alibaba/qwen-3-14b
bun run scripts/bun/models.ts unhide vercel:alibaba/qwen-3-14b

# Interactive terminal mode
bun run scripts/bun/models.ts interactive
```
