import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "shared" / "modelmd.py").exists())
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "shared"))

import modelmd  # noqa: E402


def base_price(pricing: dict, key: str):
    """Flat price, or the first tier's price when only tiers are given."""
    val = pricing.get(key)
    if val is None:
        tiers = pricing.get(f"{key}_tiers") or []
        if tiers:
            val = tiers[0].get("cost")
    return val


def price_for(m: dict) -> str:
    pricing = m.get("pricing") or {}
    p_in = base_price(pricing, "input")
    p_out = base_price(pricing, "output")
    if p_in is not None or p_out is not None:
        return modelmd.price_pair(p_in, p_out)
    if pricing.get("image") is not None:
        val = modelmd.fmt_price(pricing["image"], per_million=False)
        return f"{val}/img" if val else "-"
    return "-"


def normalize(m: dict) -> dict:
    mods = m.get("modalities") or {}
    return {
        "id": m.get("id", ""),
        "slug": m.get("id", ""),
        "price": price_for(m),
        "in_mods": mods.get("input") or [],
        "out_mods": mods.get("output") or [],
        "ctx": m.get("context_window"),
    }


def main() -> None:
    with (HERE / "models.json").open("r", encoding="utf-8") as f:
        raw = json.load(f).get("data", [])

    modelmd.run(modelmd.Provider(
        name="Vercel AI Gateway",
        base_dir=HERE,
        browse_url="https://vercel.com/ai-gateway/models",
        readme_marker="VERCEL",
        models=[normalize(m) for m in raw],
        # New tracker: don't hide the whole catalog on day one.
        hide_on_first_run=False,
    ))


if __name__ == "__main__":
    main()
