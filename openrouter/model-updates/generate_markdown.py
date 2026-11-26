import json
from pathlib import Path

BASE_DIR = Path("OpenRouter")
MODELS_FILE = BASE_DIR / "models.json"
HIDDEN_FILE = BASE_DIR / "hidden_models.json"
OUTPUT_MD = BASE_DIR / "MODELS.md"


def format_price_per_million(raw_price: str | None) -> str:
    """Converts per-token string price (e.g., '0.0000015') to '$1.50' per 1M tokens."""
    if not raw_price:
        return "N/A"
    try:
        val = float(raw_price) * 1_000_000
        if val == 0:
            return "Free"
        return f"${val:,.2f}"
    except ValueError:
        return "N/A"


def main() -> None:
    # Load models
    with MODELS_FILE.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    models = payload.get("data", [])

    # Load hidden slugs into an O(1) lookup set
    hidden_slugs: set[str] = set()
    if HIDDEN_FILE.exists():
        with HIDDEN_FILE.open("r", encoding="utf-8") as f:
            hidden_slugs = set(json.load(f))

    # Filter and sort models alphabetically by name
    visible_models = [
        m for m in models
        if m.get("canonical_slug") not in hidden_slugs
    ]
    visible_models.sort(key=lambda m: m.get("name", "").lower())

    # Build Markdown content
    lines = [
        "# OpenRouter Models",
        "",
        f"Total visible models: **{len(visible_models)}** (Hidden: {len(models) - len(visible_models)})",
        "",
        "| Model | ID | Context | Input / 1M | Output / 1M | Modalities |",
        "| :--- | :--- | ---: | ---: | ---: | :--- |",
    ]

    for m in visible_models:
        name = m.get("name", "Unknown").replace("|", "\\|")
        model_id = f"`{m.get('id', '')}`"
        ctx = f"{m.get('context_length', 0):,}"

        pricing = m.get("pricing") or {}
        prompt_price = format_price_per_million(pricing.get("prompt"))
        completion_price = format_price_per_million(pricing.get("completion"))

        arch = m.get("architecture") or {}
        modality = arch.get("modality", "N/A")

        lines.append(
            f"| {name} | {model_id} | {ctx} | {prompt_price} | {completion_price} | {modality} |"
        )

    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT_MD} with {len(visible_models)} models.")


if __name__ == "__main__":
    main()