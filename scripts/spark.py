#!/usr/bin/env python3
"""Spark Joy 数据收集 + 飞书卡片发送：LLM 负责选内容和写推荐语，脚本负责发卡片。"""

import argparse
import json
import re
import sys
import os
import urllib.request
import subprocess
import time
import socket
import random
from pathlib import Path

# 确保 uv tool 安装的命令在 PATH 中
UV_BIN = str(Path.home() / ".local" / "bin")
if UV_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = UV_BIN + os.pathsep + os.environ.get("PATH", "")

# 允许导入同目录脚本
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_all import fetch_safari_bookmarks, fetch_memo, fetch_bilibili_hot, fetch_xiaohongshu_hot
from prefs import record_history, is_recommended, get_disliked_ids, load_prefs


def parse_duration(text: str) -> float:
    """解析自然语言时长，返回分钟数。"""
    if not text:
        return 0.0
    text = text.strip().lower()

    cn_map = {
        "一刻钟": 15,
        "半小时": 30,
        "半个钟": 30,
        "半个钟头": 30,
        "一小时": 60,
        "一个钟": 60,
        "一个钟头": 60,
    }
    if text in cn_map:
        return float(cn_map[text])

    pattern = r"^([0-9]+(?:\.[0-9]+)?)\s*(分钟|min|m|小时|h|钟|钟头)?$"
    m = re.match(pattern, text)
    if not m:
        try:
            return float(text)
        except ValueError:
            return 0.0

    value = float(m.group(1))
    unit = (m.group(2) or "").lower()
    if unit in ["小时", "h", "钟", "钟头"]:
        return value * 60
    return value


def collect_items():
    """
    每次收集 60 条内容，全部交给 LLM 凭直觉选择一条：
    - 20 条小红书（随机 2 个类别，每个类别随机保留 10 条）
    - 20 条 Bilibili 热门
    - 20 条本地备忘录（随机采样）
    """
    xhs_items = fetch_xiaohongshu_hot(per_category_limit=10)
    bili_items = fetch_bilibili_hot()
    memo_items = fetch_memo(limit=20)
    return xhs_items + bili_items + memo_items


def filter_by_duration(items: list[dict], target_minutes: float) -> list[dict]:
    """筛选出时长接近 target_minutes 的内容。"""
    if target_minutes <= 0:
        return items

    scored = []
    for item in items:
        dur_sec = item.get("duration_seconds", 0)
        if dur_sec <= 0:
            scored.append((item, abs(target_minutes - 10)))
            continue

        dur_min = dur_sec / 60
        diff = abs(dur_min - target_minutes)
        if diff <= target_minutes * 0.5:
            scored.append((item, diff))
        else:
            scored.append((item, float("inf")))

    scored.sort(key=lambda x: x[1])
    return [item for item, _ in scored if _ != float("inf")] or items


def filter_recommended(items: list[dict]) -> list[dict]:
    """排除已推荐过和不喜欢的 content。"""
    disliked = get_disliked_ids()
    history = set(load_prefs().get("history", []))
    filtered = []
    for item in items:
        item_id = item.get("item_id", "")
        if not item_id:
            continue
        if item_id in disliked or item_id in history:
            continue
        filtered.append(item)
    return filtered


def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(("127.0.0.1", port))
            return True
        except ConnectionRefusedError:
            return False


def ensure_callback_server():
    """确保本地回调服务正在运行。"""
    if is_port_in_use(18789):
        return True

    server_script = Path(__file__).resolve().parent / "callback_server.py"
    if not server_script.exists():
        return False

    try:
        subprocess.Popen(
            [sys.executable, str(server_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(10):
            time.sleep(0.3)
            if is_port_in_use(18789):
                return True
    except Exception:
        pass
    return False


def get_feishu_credentials():
    """从 pi 配置中读取飞书机器人凭证。"""
    settings_path = Path.home() / ".pi" / "agent" / "settings.json"
    if not settings_path.exists():
        return None, None
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    feishu = settings.get("feishu", {})
    return feishu.get("appId", ""), feishu.get("appSecret", "")


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token。"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("code") != 0:
        raise RuntimeError(f"获取 access_token 失败: {data}")
    return data["tenant_access_token"]


def send_feishu_card(card: dict, chat_id: str) -> dict:
    """发送飞书卡片消息。"""
    app_id, app_secret = get_feishu_credentials()
    if not app_id or not app_secret:
        raise RuntimeError("未配置飞书凭证")
    token = get_tenant_access_token(app_id, app_secret)
    api_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = json.dumps({
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(card),
    }).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(
        description="Spark Joy - 数据收集 + 飞书卡片",
        epilog="示例: s, t, 推, s 5, s 半小时",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="s",
        choices=["s", "t", "推", "recommend", "开刷", "刷一刷", "逛逛", "找点乐子", "碎片时间", "推一推"],
        help="命令: s/t/推/recommend/开刷/刷一刷/逛逛/找点乐子/碎片时间/推一推=收集数据",
    )
    parser.add_argument(
        "duration",
        nargs="?",
        default="",
        help="期望的内容时长，例如: 5, 5分钟, 半小时, 1小时, 一刻钟",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式（默认）",
    )
    parser.add_argument(
        "--card",
        action="store_true",
        help="发送飞书卡片（需要配合 LLM 的推荐语）",
    )
    parser.add_argument(
        "--recommendation",
        default="",
        help="LLM 生成的推荐语文本",
    )
    parser.add_argument(
        "--url",
        default="",
        help="推荐内容的链接",
    )
    parser.add_argument(
        "--title",
        default="",
        help="推荐内容的标题",
    )
    parser.add_argument(
        "--duration-label",
        default="",
        help="时长标签，如 2分20秒、27分钟，用于卡片标题",
    )
    parser.add_argument(
        "--chat-id",
        default="",
        help="飞书 chat_id，用于 --card 模式",
    )
    parser.add_argument(
        "--item-id",
        default="",
        help="推荐内容的唯一 ID，用于记录偏好和避免重复",
    )
    parser.add_argument(
        "--content",
        default="",
        help="原始内容（用于备忘录全文推送）",
    )

    args = parser.parse_args()

    duration = parse_duration(args.duration)
    # 默认推荐 3 分钟以内的内容
    if not args.duration:
        duration = 3.0
    items = collect_items()
    # 不过滤，把全部 60 条交给 LLM 凭直觉选择
    # items = filter_by_duration(items, duration)
    # items = filter_recommended(items)

    if args.card:
        item_id = args.item_id or ""
        # 备忘录直接发全文，其余用推荐语
        if item_id.startswith("memo:") and args.content:
            card_body = args.content
        else:
            card_body = args.recommendation or "给你推荐一条内容，看看合不合现在的心情。"

        recommendation = args.recommendation or ""
        url = args.url or ""
        title = args.title or "推荐看看"
        duration_label = args.duration_label or ""
        if item_id:
            record_history(item_id)

        if duration_label:
            header_title = f"✨ {duration_label} | {title}"
        else:
            header_title = f"✨ {title}"

        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": header_title},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": card_body,
                    },
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "❤️ 喜欢，下一条"},
                            "type": "default",
                            "url": f"http://127.0.0.1:18789/callback?action=like&id={item_id}",
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "👎 不喜欢，下一条"},
                            "type": "default",
                            "url": f"http://127.0.0.1:18789/callback?action=dislike&id={item_id}",
                        },
                    ],
                },
            ],
        }

        if url:
            card["elements"].append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "🔗 点击观看"},
                        "type": "primary",
                        "url": url,
                    }
                ],
            })

        ensure_callback_server()
        chat_id = args.chat_id or "oc_b941dff6339fc3d8092c21a9c9c1763e"
        result = send_feishu_card(card, chat_id)
        if result.get("code") == 0:
            print(json.dumps({
                "ok": True,
                "message_id": result["data"]["message_id"],
                "url": url,
                "title": title,
            }, ensure_ascii=False))
        else:
            print(json.dumps({"ok": False, "error": result}, ensure_ascii=False))
            sys.exit(1)
    else:
        output = {
            "context": {
                "duration_filter": duration,
                "total": len(items),
            },
            "items": [
                {
                    "source": item.get("source"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "duration": item.get("duration"),
                    "summary": (item.get("content", "") or "").replace("\n", " ").strip()[:80],
                    "content": (item.get("content", "") or "").strip(),
                }
                for item in items
                if item.get("title") or item.get("url")
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
