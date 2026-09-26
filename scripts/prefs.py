#!/usr/bin/env python3
"""Spark Joy 用户偏好管理。"""

import json
from pathlib import Path

PREFS_DIR = Path.home() / ".private-douyin"
PREFS_FILE = PREFS_DIR / "preferences.json"


def _ensure_dir():
    PREFS_DIR.mkdir(parents=True, exist_ok=True)


def load_prefs():
    _ensure_dir()
    if PREFS_FILE.exists():
        try:
            return json.loads(PREFS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"liked": [], "disliked": [], "history": []}


def save_prefs(prefs):
    _ensure_dir()
    PREFS_FILE.write_text(
        json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def record_feedback(item_id: str, liked: bool):
    prefs = load_prefs()
    if liked:
        if item_id not in prefs["liked"]:
            prefs["liked"].append(item_id)
    else:
        if item_id not in prefs["disliked"]:
            prefs["disliked"].append(item_id)
    if item_id not in prefs["history"]:
        prefs["history"].append(item_id)
    save_prefs(prefs)


def record_history(item_id: str):
    prefs = load_prefs()
    if item_id not in prefs["history"]:
        prefs["history"].append(item_id)
        save_prefs(prefs)


def is_recommended(item_id: str) -> bool:
    return item_id in load_prefs().get("history", [])


def get_disliked_ids() -> set:
    return set(load_prefs().get("disliked", []))
