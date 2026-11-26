"""Shared engine for the model trackers (OpenRouter, Vercel AI Gateway, ...).

Each tracker normalises its catalog into dicts shaped like:
    {"id": str, "slug": str, "price": str,
     "in_mods": [str], "out_mods": [str], "ctx": int | None}
and passes them to run().
"""
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent
ROOT = SHARED_DIR.parent
ICON_DIR = SHARED_DIR / "icons"
SETTINGS_FILE = SHARED_DIR / "settings.json"
README = ROOT / "README.md"

ICON_SIZE = 16
DEFAULT_ICON_MODE = "svg"  # overridden by shared/settings.json

EMOJI = {
    "text": "💬",
    "image": "🖼️",
    "file": "📄",
    "audio": "🎧",
    "video": "🎬",
}
ALIASES = {"pdf": "file"}
LEGEND = [
    ("text", "text"),
    ("image", "image"),
    ("file", "file / pdf"),
    ("audio", "audio"),
    ("video", "video"),
]

_SVG_HEAD = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
)

# Mid-tone colors that read on both light and dark GitHub themes.
SVGS = {
    "text": _SVG_HEAD.format(c="#3b82f6")
    + '<path d="M4 7V5h16v2M12 5v14M9 19h6"/></svg>',
    "image": _SVG_HEAD.format(c="#22c55e")
    + '<rect x="3" y="3" width="18" height="18" rx="2"/>'
    '<circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/></svg>',
    "file": _SVG_HEAD.format(c="#f59e0b")
    + '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
    '<path d="M14 3v5h5"/></svg>',
    "audio": _SVG_HEAD.format(c="#a855f7")
    + '<path d="M3 14v-2a9 9 0 0 1 18 0v2"/>'
    '<path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z"/>'
    '<path d="M3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>',
    "video": _SVG_HEAD.format(c="#ef4444")
    + '<rect x="2" y="5" width="14" height="14" rx="2"/>'
    '<path d="m22 8-6 4 6 4z"/></svg>',
}


@dataclass
class Provider:
    name: str                  # "OpenRouter"
    base_dir: Path             # folder holding the json state files + MODELS.md
    browse_url: str            # link to the provider's own model page
    readme_marker: str         # "OPENROUTER" -> <!-- OPENROUTER:START --> ... :END -->
    models: list[dict]         # normalised models (see module docstring)
    hide_on_first_run: bool = True


# ---------- icons / settings ----------

def icon_mode() -> str:
    try:
        mode = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))["icon_mode"]
    except (OSError, ValueError, KeyError):
        mode = DEFAULT_ICON_MODE
    return mode if mode in ("svg", "emoji") else DEFAULT_ICON_MODE


def ensure_icons() -> None:
    """Write icon files if missing. Existing files are never overwritten."""
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    for name, svg in SVGS.items():
        path = ICON_DIR / f"{name}.svg"
        if not path.exists():
            path.write_text(svg + "\n", encoding="utf-8")


def icon(mod: str, mode: str, rel: str) -> str:
    name = ALIASES.get(mod, mod)
    if mode == "svg" and name in SVGS:
        return (
            f'<img src="{rel}/{name}.svg" width="{ICON_SIZE}" '
            f'height="{ICON_SIZE}" alt="{name}" title="{name}">'
        )
    return EMOJI.get(name, mod)


def icons(mods: list[str], mode: str, rel: str) -> str:
    return "".join(icon(x, mode, rel) for x in mods) or "-"


def legend(mode: str, rel: str) -> str:
    return " · ".join(f"{icon(k, mode, rel)} {label}" for k, label in LEGEND)


# ---------- formatting ----------

def fmt_price(raw, per_million: bool = True) -> str | None:
    """Raw price -> '$0.15', 'Free', 'varies', or None when missing."""
    if raw is None or raw == "":
        return None
    try:
        val = float(raw) * (1_000_000 if per_million else 1)
    except (TypeError, ValueError):
        return None
    if val < 0:
        return "varies"  # router models report negative placeholder prices
    if val == 0:
        return "Free"
    s = f"{val:.4f}".rstrip("0")
    whole, _, frac = s.partition(".")
    return f"${whole}.{frac.ljust(2, '0')}"


def price_pair(raw_in, raw_out) -> str:
    p_in, p_out = fmt_price(raw_in), fmt_price(raw_out)
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


# ---------- state files ----------

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


# ---------- README ----------

def update_readme(p: Provider, listed: int, new: int, hidden: int) -> None:
    start = f"<!-- {p.readme_marker}:START -->"
    end = f"<!-- {p.readme_marker}:END -->"
    md_link = Path(os.path.relpath(p.base_dir / "MODELS.md", ROOT)).as_posix()
    synced = time.strftime("%Y-%m-%d", time.gmtime())
    block = (
        f"{start}\n"
        "| Listed | 🆕 Unseen | Hidden |\n"
        "| :-: | :-: | :-: |\n"
        f"| [**{listed}**]({md_link}) | **{new}** | **{hidden}** |\n"
        "\n"
        f"Last sync {synced} UTC · [Browse all models on {p.name}]({p.browse_url})\n"
        f"{end}"
    )
    text = README.read_text(encoding="utf-8") if README.exists() else ""
    if start in text and end in text:
        text = re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            lambda _: block,
            text,
            flags=re.S,
        )
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    README.write_text(text, encoding="utf-8")


# ---------- main engine ----------

def run(p: Provider) -> None:
    now = int(time.time())
    base = p.base_dir
    allowed_file = base / "allowed_models.json"
    hidden_file = base / "hidden_models.json"
    seen_file = base / "seen_models.json"
    md_file = base / "MODELS.md"

    is_initial_run = not seen_file.exists()
    mark_seen = os.environ.get("MARK_SEEN", "").lower() == "true"
    to_hide = {
        h.strip() for h in os.environ.get("HIDE", "").split(",") if h.strip()
    }

    mode = icon_mode()
    if mode == "svg":
        ensure_icons()
    rel = Path(os.path.relpath(ICON_DIR, md_file.parent)).as_posix()

    models = [m for m in p.models if m.get("id")]
    allowed_set = set(load_json_list(allowed_file))
    hidden_set = set(load_json_list(hidden_file))
    seen_map = load_seen_map(seen_file)

    # Allowlisted models can never be hidden
    hidden_set = {h for h in hidden_set if h not in allowed_set}
    hidden_set |= {h for h in to_hide if h not in allowed_set}

    def is_allowed(m: dict) -> bool:
        return m["id"] in allowed_set or m["slug"] in allowed_set

    def is_hidden(m: dict) -> bool:
        return m["id"] in hidden_set or m["slug"] in hidden_set

    for m in models:
        if is_allowed(m):
            seen_map.setdefault(m["id"], now)
        elif is_initial_run:
            # First run: everything counts as seen, optionally hidden too
            if p.hide_on_first_run:
                hidden_set.add(m["slug"])
            seen_map[m["id"]] = now

    visible = [m for m in models if is_allowed(m) or not is_hidden(m)]

    # "New" = visible, not allowlisted, and not yet acknowledged by you
    new_keys = {
        m["id"] for m in visible
        if not is_allowed(m) and m["id"] not in seen_map
    }

    if mark_seen:
        for m in visible:
            seen_map.setdefault(m["id"], now)
        new_keys = set()

    visible.sort(key=lambda m: (
        0 if is_allowed(m) else 1 if m["id"] in new_keys else 2,
        m["id"].lower(),
    ))
    hidden_count = len(models) - len(visible)

    hidden_file.write_text(
        json.dumps(sorted(hidden_set), indent=2) + "\n", encoding="utf-8"
    )
    seen_file.write_text(
        json.dumps(dict(sorted(seen_map.items())), indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        f"# {p.name} Models",
        "",
        f"**{len(visible)}** listed · 🆕 **{len(new_keys)}** unseen · "
        f"**{hidden_count}** hidden · [browse all on {p.name}]({p.browse_url})",
        "",
        f"⭐ allowlisted · 🆕 unseen · {legend(mode, rel)} · "
        "prices are $ per 1M tokens (input → output)",
        "",
        "| | Model | Price (in → out) | In | Out | Ctx |",
        "| :-: | :--- | :--- | :-: | :-: | ---: |",
    ]

    for m in visible:
        if is_allowed(m):
            status = "⭐"
        elif m["id"] in new_keys:
            status = "🆕"
        else:
            status = ""
        lines.append(
            f"| {status} | `{m['id']}` | {m['price']} "
            f"| {icons(m['in_mods'], mode, rel)} | {icons(m['out_mods'], mode, rel)} "
            f"| {fmt_context(m['ctx'])} |"
        )

    md_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    update_readme(p, len(visible), len(new_keys), hidden_count)
    print(
        f"{p.name}: listed {len(visible)} | unseen {len(new_keys)} | "
        f"hidden {hidden_count} | icons {mode}"
    )
