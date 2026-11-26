import json
import time
from pathlib import Path

BASE_DIR = Path("openrouter/model-updates")
MODELS_FILE = BASE_DIR / "models.json"
ALLOWED_FILE = BASE_DIR / "allowed_models.json"
HIDDEN_FILE = BASE_DIR / "hidden_models.json"
SEEN_FILE = BASE_DIR / "seen_models.json"
OUTPUT_MD = BASE_DIR / "MODELS.md"

# Set to an integer (e.g., 7) to auto-hide new releases after N days if not allowlisted,
# or None to keep new releases visible indefinitely until you manually hide them.
NEW_RELEASE_GRACE_DAYS: int | None = None


def load_json_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_seen_map(path: Path) -> dict[str, int]:
    """Maps model id -> unix timestamp when first seen."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            now = int(time.time())
            return {item: now for item in data}
        return data


def is_in_set(model: dict, lookup: set[str]) -> bool:
    model_id = model.get("id", "")
    slug = model.get("canonical_slug", "")
    # Match exact id, exact canonical_slug, or base id without ':free'
    base_id = model_id.split(":")[0]
    return (
        model_id in lookup
        or slug in lookup
        or (base_id in lookup and model_id in lookup)
    )


def format_price_per_million(raw_price: str | None) -> str:
    if not raw_price:
        return "N/A"
    try:
        val = float(raw_price) * 1_000_000
        return "Free" if val == 0 else f"${val:,.2f}"
    except ValueError:
        return "N/A"


def main() -> None:
    now = int(time.time())
    is_initial_run = not SEEN_FILE.exists()

    with MODELS_FILE.open("r", encoding="utf-8") as f:
        models = json.load(f).get("data", [])

    allowed_set = set(load_json_list(ALLOWED_FILE))
    hidden_set = set(load_json_list(HIDDEN_FILE))
    seen_map = load_seen_map(SEEN_FILE)

    # Ensure allowlisted models are never trapped in hidden_models.json
    hidden_set = {
        h for h in hidden_set if h not in allowed_set
    }

    new_releases: list[str] = []

    for m in models:
        model_id = m.get("id", "")
        slug = m.get("canonical_slug", "")
        key = model_id or slug
        if not key:
            continue

        is_allowed = model_id in allowed_set or slug in allowed_set

        if is_allowed:
            seen_map.setdefault(key, now)
            continue

        if is_initial_run:
            # First run: hide everything not in allowed_models.json
            hidden_set.add(slug or model_id)
            seen_map[key] = now
        elif key not in seen_map:
            # Brand-new model discovered after initial run -> keep visible!
            seen_map[key] = now
            new_releases.append(model_id)
        else:
            # Previously seen model: only auto-hide if grace window expired
            if NEW_RELEASE_GRACE_DAYS is not None:
                age_days = (now - seen_map[key]) / 86400
                if age_days >= NEW_RELEASE_GRACE_DAYS:
                    hidden_set.add(slug or model_id)

    # Persist updated state files sorted for clean git diffs
    HIDDEN_FILE.write_text(
        json.dumps(sorted(hidden_set), indent=2) + "\n", encoding="utf-8"
    )
    SEEN_FILE.write_text(
        json.dumps(dict(sorted(seen_map.items())), indent=2) + "\n", encoding="utf-8"
    )

    # Filter visible models for Markdown
    visible_models = [
        m for m in models
        if (m.get("id") in allowed_set or m.get("canonical_slug") in allowed_set)
        or (m.get("id") not in hidden_set and m.get("canonical_slug") not in hidden_set)
    ]
    visible_models.sort(key=lambda m: (
        0 if (m.get("id") in allowed_set or m.get("canonical_slug") in allowed_set) else 1,
        m.get("name", "").lower(),
    ))

    lines = [
        "# OpenRouter Models",
        "",
        f"Visible: **{len(visible_models)}** | Hidden: **{len(hidden_set)}**",
        "",
        "| Status | Model | ID | Context | Input / 1M | Output / 1M | Modalities |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | :--- |",
    ]

    for m in visible_models:
        model_id = m.get("id", "")
        slug = m.get("canonical_slug", "")
        status = "Allowlisted" if (model_id in allowed_set or slug in allowed_set) else "🆕 New"
        name = m.get("name", "Unknown").replace("|", "\\|")
        ctx = f"{m.get('context_length', 0):,}"

        pricing = m.get("pricing") or {}
        prompt_price = format_price_per_million(pricing.get("prompt"))
        completion_price = format_price_per_million(pricing.get("completion"))

        arch = m.get("architecture") or {}
        modality = arch.get("modality", "N/A")

        lines.append(
            f"| {status} | {name} | `{model_id}` | {ctx} | {prompt_price} | {completion_price} | {modality} |"
        )

    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Visible: {len(visible_models)} | Hidden: {len(hidden_set)} | New this run: {len(new_releases)}")


if __name__ == "__main__":
    main()