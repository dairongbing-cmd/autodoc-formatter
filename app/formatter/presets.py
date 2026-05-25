import json
from pathlib import Path

from app.config import PRESETS_DIR
from app.models.rules import FormattingRules


def list_presets() -> list[dict]:
    presets = []
    if not PRESETS_DIR.exists():
        return presets
    for f in sorted(PRESETS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            presets.append({
                "name": f.stem,
                "label": data.get("label", f.stem),
                "description": data.get("description", ""),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return presets


def load_preset(name: str) -> FormattingRules | None:
    file_path = PRESETS_DIR / f"{name}.json"
    if not file_path.exists():
        return None
    data = json.loads(file_path.read_text(encoding="utf-8"))
    rules_data = data.get("rules", data)
    if "preset_name" not in rules_data:
        rules_data["preset_name"] = name
    return FormattingRules(**rules_data)
