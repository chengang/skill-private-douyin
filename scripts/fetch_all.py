#!/usr/bin/env python3
"""从多个来源收集用户的收藏内容，统一输出为 JSON。"""

import json
import random
import subprocess
import sys
import os
from pathlib import Path

# 确保 uv tool 安装的命令在 PATH 中
UV_BIN = str(Path.home() / ".local" / "bin")
if UV_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = UV_BIN + os.pathsep + os.environ.get("PATH", "")


def run(cmd: str, **kwargs) -> str | None:
    """运行 shell 命令，成功时返回 stdout，失败返回 None。"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            **kwargs,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except Exception:
        return None


def _make_item_id(source: str, key: str) -> str:
    return f"{source}:{key}"


def fetch_safari_bookmarks() -> list[dict]:
    """获取 Safari 书签（仅 URL 书签，不含文件夹）。"""
    out = run('safari-bookmarks list --format "{title}\\\\t{url}\\\\t{type}"')
    if not out:
        return []

    items = []
    for line in out.splitlines():
        parts = line.split("\\\\t", 2)
        if len(parts) < 3:
            continue
        title, url, kind = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if kind != "bookmark" or not url:
            continue
        items.append({
            "source": "safari",
            "item_id": _make_item_id("safari", url),
            "type": "bookmark",
            "title": title or url,
            "url": url,
            "content": f"{title}\n{url}" if title else url,
        })
    return items


LOCAL_MEMO_FOLDERS = [
    "想读的文章",
    "旅行灵感",
    "学习笔记",
    "生活清单",
    "治愈瞬间",
    "工作灵感",
    "美食记录",
    "影评收藏",
]

# 笔记分隔符（避免与正文中的换行冲突）
_NOTE_SEP = "|||NOTE_SEP|||"


def fetch_memo(limit: int = 0) -> list[dict]:
    """
    获取 macOS 备忘录内容（仅本地文件夹，排除 iCloud）。
    通过 AppleScript 按文件夹批量读取，速度远快于逐条调用 memo CLI。
    """
    items = []
    for folder in LOCAL_MEMO_FOLDERS:
        script = f'''
        tell application "Notes"
            set output to ""
            try
                set targetFolder to folder "{folder}"
                repeat with n in notes of targetFolder
                    set output to output & name of n & "\t" & body of n & "{_NOTE_SEP}"
                end repeat
            end try
            return output
        end tell
        '''
        out = run(f"osascript -e '{script}'")
        if not out:
            continue
        # 用特殊分隔符分割每条笔记
        for note_block in out.split(_NOTE_SEP):
            note_block = note_block.strip()
            if not note_block:
                continue
            parts = note_block.split("\t", 1)
            title = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else ""
            if not title or title.startswith("<div") or title.startswith("<font"):
                continue
            import re
            body = re.sub(r"<[^>]+>", "", body)
            body = re.sub(r"\s+", " ", body).strip()
            if not body:
                body = title
            items.append({
                "source": "memo",
                "item_id": _make_item_id("memo", f"{folder}|{title}"),
                "type": "note",
                "title": title,
                "url": "",
                "content": body,
            })

    # 随机采样
    if limit > 0 and len(items) > limit:
        items = random.sample(items, limit)
    return items


def fetch_bilibili_hot() -> list[dict]:
    """获取 Bilibili 热门视频（公开 API，无需登录）。"""
    out = run("bili hot -n 20 --json")
    if not out:
        return []

    items = []
    try:
        data = json.loads(out)
        if isinstance(data, dict) and "data" in data:
            video_list = data["data"].get("items", [])
            for v in video_list:
                items.append({
                    "source": "bilibili",
                    "item_id": _make_item_id("bilibili", v.get("url", "").split("/")[-1]),
                    "type": "video",
                    "title": v.get("title", ""),
                    "url": v.get("url", ""),
                    "content": v.get("description", v.get("title", "")),
                    "duration_seconds": v.get("duration_seconds", 0),
                    "duration": v.get("duration", ""),
                    "owner": v.get("owner", {}).get("name", ""),
                    "stats": v.get("stats", {}),
                })
    except Exception:
        pass
    return items


XHS_CATEGORIES = [
    "fashion",
    "food",
    "travel",
    "fitness",
    "movie",
    "career",
    "love",
    "home",
    "gaming",
    "cosmetics",
]


def fetch_xiaohongshu_hot(categories: list[str] | None = None, per_category_limit: int = 10) -> list[dict]:
    """
    获取小红书热门笔记。
    - categories: 要获取的类别列表，None 则随机选 2 个
    - per_category_limit: 每个类别随机保留的条目数
    """
    if categories is None:
        categories = random.sample(XHS_CATEGORIES, 2)

    items = []
    seen_ids: set[str] = set()
    for category in categories:
        out = run(f"xhs hot -c {category} --json")
        if not out:
            continue
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("ok") is not True:
            continue
        notes = data.get("data", {}).get("items", [])
        # 随机丢弃一半，保留 per_category_limit 条
        if len(notes) > per_category_limit:
            notes = random.sample(notes, per_category_limit)
        for note in notes:
            note_card = note.get("note_card", {})
            note_id = note.get("id", "")
            if not note_id or note_id in seen_ids:
                continue
            seen_ids.add(note_id)

            title = note_card.get("display_title", "")
            user = note_card.get("user", {})
            nick_name = user.get("nick_name", "") or user.get("nickname", "")

            url = f"https://www.xiaohongshu.com/explore?note_id={note_id}"

            duration_seconds = 0
            video_info = note_card.get("video", {})
            if isinstance(video_info, dict):
                capa = video_info.get("capa", {})
                if isinstance(capa, dict):
                    duration_seconds = capa.get("duration", 0)

            content_parts = [title]
            if nick_name:
                content_parts.append(f"by {nick_name}")
            interact = note_card.get("interact_info", {})
            if isinstance(interact, dict):
                like_count = interact.get("liked_count", "")
                if like_count:
                    content_parts.append(f"👍 {like_count}")

            items.append({
                "source": "xiaohongshu",
                "item_id": _make_item_id("xhs", note_id),
                "type": "note",
                "title": title,
                "url": url,
                "content": " | ".join(content_parts),
                "duration_seconds": duration_seconds,
                "duration": f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds else "",
                "category": category,
                "owner": nick_name,
                "stats": interact if isinstance(interact, dict) else {},
            })
    return items


def main() -> None:
    """
    每次收集 60 条内容：
    - 20 条小红书（随机 2 个类别，每个类别随机保留 10 条）
    - 20 条 Bilibili 热门
    - 20 条本地备忘录（随机采样）
    全部交给 LLM 凭直觉选择一条。
    """
    xhs_items = fetch_xiaohongshu_hot(per_category_limit=10)  # 2 类别 × 10 = 20
    bili_items = fetch_bilibili_hot()  # 20
    memo_items = fetch_memo(limit=20)  # 随机 20

    items = xhs_items + bili_items + memo_items

    for idx, item in enumerate(items):
        item["id"] = idx + 1

    print(json.dumps(items, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
