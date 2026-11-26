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

MODALITY_ICONS = {
    "text": "💬",
    "image": "🖼️",
    "file": "📄",
    "audio": "🎧",
    "video": "🎬",
}


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


# ---------- formatting helpers ----------

def fmt_price(raw: str | None) -> str | None:
    """Per-token price string -> '$0.15' per 1M tokens, 'Free', or 'varies'."""
    if raw is None or raw == "":
        return None
    try:
        val = float(raw) * 1_000_000
    except ValueError:
        return None
    if val < 0:
        return "varies"  # router models report negative placeholder prices
    if val == 0:
        return "Free"
    s = f"{val:.4f}".rstrip("0")
    whole, _, frac = s.partition(".")
    return f"${whole}.{frac.ljust(2, '0')}"


def fmt_price_pair(pricing: dict) -> str:
    p_in = fmt_price(pricing.get("prompt"))
    p_out = fmt_price(pricing.get("completion"))
    if p_in is None and p_out is None:
        return "-"
    if p_in == p_out == "Free":
        return "Free"
    return f"{p_in or '-'} → {p_out or '-'}"


def fmt_context(n: int | None) -> str:
    if not n:
        return "-"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.3g}M"
    if n >= 1_000:
        return f"{n / 1_000:.3g}K"
    return str(n)


def icons(mods: list[str]) -> str:
    return "".join(MODALITY_ICONS.get(x, "❔") for x in mods) or "❔"


def fmt_modalities(arch: dict) -> str:
    ins = arch.get("input_modalities")
    outs = arch.get("output_modalities")
    if not ins or not outs:
        # Fallback: parse strings like "text+image->text"
        raw = arch.get("modality") or ""
        left, _, right = raw.partition("->")
        ins = [x for x in left.split("+") if x]
        outs = [x for x in right.split("+") if x]
    if not ins and not outs:
        return "-"
    return f"{icons(ins)} → {icons(outs)}"


# ---------- README ----------

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


# ---------- main ----------

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
        model_key(m).lower(),
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
        f"**{len(visible)}** listed · 🆕 **{len(new_keys)}** unseen · **{hidden_count}** hidden · "
        f"[browse all on OpenRouter]({OPENROUTER_URL})",
        "",
        "⭐ allowlisted · 🆕 unseen · "
        "💬 text · 🖼️ image · 📄 file · 🎧 audio · 🎬 video · "
        "prices are $ per 1M tokens (input → output)",
        "",
        "| | Model | Price (in → out) | Modalities | Ctx |",
        "| :-: | :--- | :--- | :-: | ---: |",
    ]

    for m in visible:
        if is_allowed(m):
            status = "⭐"
        elif model_key(m) in new_keys:
            status = "🆕"
        else:
            status = ""
        pricing = m.get("pricing") or {}
        arch = m.get("architecture") or {}
        lines.append(
            f"| {status} | `{m.get('id', '')}` | {fmt_price_pair(pricing)} "
            f"| {fmt_modalities(arch)} | {fmt_context(m.get('context_length'))} |"
        )

    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    update_readme(len(visible), len(new_keys), hidden_count)
    print(f"Listed: {len(visible)} | Unseen: {len(new_keys)} | Hidden: {hidden_count}")


if __name__ == "__main__":
    main()
