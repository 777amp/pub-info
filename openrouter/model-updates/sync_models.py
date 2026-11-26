import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(
    p for p in HERE.parents
    if (p / "shared" / "modelmd.py").exists()
)

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "shared"))

import modelmd  # noqa: E402


def normalize(m: dict) -> dict:
    architecture = m.get("architecture") or {}
    pricing = m.get("pricing") or {}

    input_mods = architecture.get("input_modalities") or []
    output_mods = architecture.get("output_modalities") or []

    if not input_mods or not output_mods:
        raw = architecture.get("modality") or ""
        left, _, right = raw.partition("->")

        input_mods = input_mods or [
            x for x in left.split("+") if x
        ]

        output_mods = output_mods or [
            x for x in right.split("+") if x
        ]

    return {
        "id": m.get("id") or m.get("canonical_slug") or "",
        "slug": m.get("canonical_slug") or m.get("id") or "",
        "price": modelmd.price_pair(
            pricing.get("prompt"),
            pricing.get("completion"),
        ),
        "in_mods": input_mods,
        "out_mods": output_mods,
        "ctx": m.get("context_length"),
    }


def main() -> None:
    with (HERE / "models.json").open("r", encoding="utf-8") as f:
        raw = json.load(f).get("data", [])

    models = [
        normalize(m)
        for m in raw
        if m.get("id") or m.get("canonical_slug")
    ]

    modelmd.run(
        modelmd.Provider(
            name="OpenRouter",
            base_dir=HERE,
            browse_url="https://openrouter.ai/models",
            readme_marker="OPENROUTER",
            models=models,
            hide_on_first_run=False,
        )
    )


if __name__ == "__main__":
    main()