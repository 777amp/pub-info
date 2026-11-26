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
DEFAULT_ICON_MODE = "svg"

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
    "pending": _SVG_HEAD.format(c="#f59e0b")
    + '<circle cx="12" cy="12" r="9"/>'
    '<path d="M12 7v5l3 2"/></svg>',
}


@dataclass
class Provider:
    name: str
    base_dir: Path
    browse_url: str
    readme_marker: str
    models: list[dict]
    hide_on_first_run: bool = True


# ---------- icons / settings ----------

def icon_mode() -> str:
    try:
        mode = json.loads(
            SETTINGS_FILE.read_text(encoding="utf-8")
        )["icon_mode"]
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


def pending_icon(mode: str, rel: str) -> str:
    if mode == "svg":
        return (
            f'<img src="{rel}/pending.svg" width="{ICON_SIZE}" '
            'height="{ICON_SIZE}" alt="pending" title="Needs review">'
        )

    return "🕒"


def legend(mode: str, rel: str) -> str:
    return " · ".join(
        f"{icon(k, mode, rel)} {label}"
        for k, label in LEGEND
    )


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
        return "varies"

    if val == 0:
        return "Free"

    s = f"{val:.4f}".rstrip("0")
    whole, _, frac = s.partition(".")
    return f"${whole}.{frac.ljust(2, '0')}"


def price_pair(raw_in, raw_out) -> str:
    p_in = fmt_price(raw_in)
    p_out = fmt_price(raw_out)

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
    """Load legacy seen-state data for backward compatibility."""
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        now = int(time.time())
        return {item: now for item in data}

    return data


# ---------- README ----------

def update_readme(
    p: Provider,
    listed: int,
    pending: int,
    hidden: int,
) -> None:
    start = f"<!-- {p.readme_marker}:START -->"
    end = f"<!-- {p.readme_marker}:END -->"

    md_link = Path(
        os.path.relpath(p.base_dir / "MODELS.md", ROOT)
    ).as_posix()

    synced = time.strftime("%Y-%m-%d", time.gmtime())

    block = (
        f"{start}\n"
        "| Listed | 🕒 Pending review | Hidden |\n"
        "| :-: | :-: | :-: |\n"
        f"| [**{listed}**]({md_link}) | **{pending}** | **{hidden}** |\n"
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
    base = p.base_dir

    allowed_file = base / "allowed_models.json"
    hidden_file = base / "hidden_models.json"
    seen_file = base / "seen_models.json"
    md_file = base / "MODELS.md"

    # Only a manual workflow_dispatch run applies the allowlist as a
    # complete approval decision.
    review_allowlist = (
        os.environ.get("REVIEW_ALLOWLIST", "").lower() == "true"
    )

    to_hide = {
        h.strip()
        for h in os.environ.get("HIDE", "").split(",")
        if h.strip()
    }

    mode = icon_mode()

    if mode == "svg":
        ensure_icons()

    rel = Path(
        os.path.relpath(ICON_DIR, md_file.parent)
    ).as_posix()

    models = [
        m for m in p.models
        if m.get("id")
    ]

    allowed_set = set(load_json_list(allowed_file))
    hidden_set = set(load_json_list(hidden_file))
    seen_map = load_seen_map(seen_file)

    def is_allowed(m: dict) -> bool:
        return (
            m["id"] in allowed_set
            or m["slug"] in allowed_set
        )

    def model_keys(m: dict) -> set[str]:
        return {
            m["id"],
            m["slug"],
        }

    # Allowlisted models must never remain hidden.
    hidden_set = {
        h for h in hidden_set
        if h not in allowed_set
    }

    # Preserve explicit manual hide support.
    # Allowlisted models cannot be hidden this way either.
    hidden_set |= {
        h for h in to_hide
        if h not in allowed_set
    }

    # A manual run treats the allowlist as the approval list:
    # every discovered model not on it becomes hidden.
    if review_allowlist:
        for m in models:
            if not is_allowed(m):
                hidden_set.update(model_keys(m))

    # Remove both ID and slug from hidden state for approved models.
    for m in models:
        if is_allowed(m):
            hidden_set.difference_update(model_keys(m))

    visible = [
        m for m in models
        if is_allowed(m) or not (model_keys(m) & hidden_set)
    ]

    # Pending review means visible but not allowlisted.
    pending_keys = {
        m["id"]
        for m in visible
        if not is_allowed(m)
    }

    # Retain timestamps for compatibility with existing seen_models.json.
    for m in models:
        if is_allowed(m):
            seen_map.setdefault(m["id"], int(time.time()))

    # Approved models appear first, followed by pending models.
    visible.sort(
        key=lambda m: (
            0 if is_allowed(m) else 1,
            m["id"].lower(),
        )
    )

    hidden_count = len(models) - len(visible)

    hidden_file.write_text(
        json.dumps(sorted(hidden_set), indent=2) + "\n",
        encoding="utf-8",
    )

    seen_file.write_text(
        json.dumps(dict(sorted(seen_map.items())), indent=2) + "\n",
        encoding="utf-8",
    )

    pending = pending_icon(mode, rel)

    lines = [
        f"# {p.name} Models",
        "",
        f"**{len(visible)}** listed · "
        f"🕒 **{len(pending_keys)}** pending review · "
        f"**{hidden_count}** hidden · "
        f"[browse all on {p.name}]({p.browse_url})",
        "",
        f"⭐ allowlisted · {pending} needs review · "
        f"{legend(mode, rel)} · "
        "prices are $ per 1M tokens (input → output)",
        "",
        "| | Model | Price (in → out) | In | Out | Ctx |",
        "| :-: | :--- | :--- | :-: | :-: | ---: |",
    ]

    for m in visible:
        status = "⭐" if is_allowed(m) else pending

        lines.append(
            f"| {status} | `{m['id']}` | {m['price']} "
            f"| {icons(m['in_mods'], mode, rel)} "
            f"| {icons(m['out_mods'], mode, rel)} "
            f"| {fmt_context(m['ctx'])} |"
        )

    md_file.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    update_readme(
        p,
        len(visible),
        len(pending_keys),
        hidden_count,
    )

    print(
        f"{p.name}: listed {len(visible)} | "
        f"pending review {len(pending_keys)} | "
        f"hidden {hidden_count} | icons {mode}"
    )