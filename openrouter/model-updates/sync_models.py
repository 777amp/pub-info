import json
import os
import re
import time
from pathlib import Path

BASE_DIR = Path("openrouter/model-updates")
MODELS_FILE = BASE_DIR / "models.json"
ALLOWED_FILE = BASE_DIR / "allowed_models.json"
HIDDEN_FILE = BASE_DIR / "hidden_models.json"
SEEN_FILE = BASE_DIR / "seen_models.json"
OUTPUT_MD = BASE_DIR / "MODELS.md"
README = Path("README.md")

OPENROUTER_URL = "https://openrouter.ai/models"
MODELS_MD_LINK = "openrouter/model-updates/MODELS.md"
README_START = "<!-- MODELS:START -->"
README_END = "<!-- MODELS:END -->"


def load_json_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_seen_map(path: Path) -> dict[str, int]:
    """Maps model id -> unix timestamp when you acknowledged it."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            now = int(time.time())
            return {item: now for item in data}
        return data


def model_key(m: dict) -> str:
    return m.get("id") or m.get("canonical_slug") or ""


def format_price_per_million(raw_price: str | None) -> str:
    if not raw_price:
        return "N/A"
    try:
        val = float(raw_price) * 1_000_000
        return "Free" if val == 0 else f"${val:,.2f}"
    except ValueError:
        return "N/A"


def update_readme(visible: int, new: int, hidden: int) -> None:
    block = (
        f"{README_START}\n"
        f"**[OpenRouter models]({OPENROUTER_URL})**: "
        f"[{visible} listed]({MODELS_MD_LINK}) · "
        f"🆕 {new} unseen · {hidden} hidden\n"
        f"{README_END}"
    )
    text = README.read_text(encoding="utf-8") if README.exists() else ""
    if README_START in text and README_END in text:
        text = re.sub(
            re.escape(README_START) + r".*?" + re.escape(README_END),
            lambda _: block,
            text,
            flags=re.S,
        )
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    README.write_text(text, encoding="utf-8")


def main() -> None:
    now = int(time.time())
    is_initial_run = not SEEN_FILE.exists()
    mark_seen = os.environ.get("MARK_SEEN", "").lower() == "true"
    to_hide = {
        h.strip() for h in os.environ.get("HIDE", "").split(",") if h.strip()
    }

    with MODELS_FILE.open("r", encoding="utf-8") as f:
        models = json.load(f).get("data", [])

    allowed_set = set(load_json_list(ALLOWED_FILE))
    hidden_set = set(load_json_list(HIDDEN_FILE))
    seen_map = load_seen_map(SEEN_FILE)

    # Allowlisted models can never be hidden
    hidden_set = {h for h in hidden_set if h not in allowed_set}
    hidden_set |= {h for h in to_hide if h not in allowed_set}

    def is_allowed(m: dict) -> bool:
        return m.get("id") in allowed_set or m.get("canonical_slug") in allowed_set

    def is_hidden(m: dict) -> bool:
        return m.get("id") in hidden_set or m.get("canonical_slug") in hidden_set

    for m in models:
        key = model_key(m)
        if not key:
            continue
        if is_allowed(m):
            seen_map.setdefault(key, now)
        elif is_initial_run:
            # First run: hide everything not allowlisted, treat all as seen
            hidden_set.add(m.get("canonical_slug") or key)
            seen_map[key] = now

    visible = [m for m in models if is_allowed(m) or not is_hidden(m)]

    # "New" = visible, not allowlisted, and not yet acknowledged by you
    new_keys = {
        model_key(m) for m in visible
        if not is_allowed(m) and model_key(m) not in seen_map
    }

    if mark_seen:
        for m in visible:
            seen_map.setdefault(model_key(m), now)
        new_keys = set()

    visible.sort(key=lambda m: (
        0 if is_allowed(m) else 1 if model_key(m) in new_keys else 2,
        m.get("name", "").lower(),
    ))
    hidden_count = len(models) - len(visible)

    HIDDEN_FILE.write_text(
        json.dumps(sorted(hidden_set), indent=2) + "\n", encoding="utf-8"
    )
    SEEN_FILE.write_text(
        json.dumps(dict(sorted(seen_map.items())), indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# OpenRouter Models",
        "",
        f"Listed: **{len(visible)}** | 🆕 Unseen: **{len(new_keys)}** | Hidden: **{hidden_count}**",
        "",
        f"Browse everything on [OpenRouter]({OPENROUTER_URL}).",
        "",
        "| Status | Model | ID | Context | Input / 1M | Output / 1M | Modalities |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | :--- |",
    ]

    for m in visible:
        model_id = m.get("id", "")
        if is_allowed(m):
            status = "⭐ Allowlisted"
        elif model_key(m) in new_keys:
            status = "🆕 New"
        else:
            status = "Seen"
        name = m.get("name", "Unknown").replace("|", "\\|")
        ctx = f"{m.get('context_length', 0):,}"
        pricing = m.get("pricing") or {}
        prompt_price = format_price_per_million(pricing.get("prompt"))
        completion_price = format_price_per_million(pricing.get("completion"))
        modality = (m.get("architecture") or {}).get("modality", "N/A")
        lines.append(
            f"| {status} | {name} | `{model_id}` | {ctx} | {prompt_price} | {completion_price} | {modality} |"
        )

    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    update_readme(len(visible), len(new_keys), hidden_count)
    print(f"Listed: {len(visible)} | Unseen: {len(new_keys)} | Hidden: {hidden_count}")


if __name__ == "__main__":
    main()
