# 数据源 Schema

> 本文件定义了所有数据源的返回格式、字段说明和已知限制。开发新数据源时必须遵循 `item_id` 格式规范。

## 统一 Item 结构

```json
{
  "source": "string",
  "item_id": "string",
  "type": "video | text | article",
  "title": "string",
  "url": "string",
  "content": "string",
  "duration_seconds": "number",
  "duration": "string",
  "owner": "string",
  "stats": "object",
  "category": "string",
  "summary": "string"
}
```

## 必填字段

| 字段 | 说明 |
|------|------|
| `source` | 数据源标识，如 `bilibili`、`xiaohongshu`、`memo`、`safari` |
| `item_id` | 全局唯一 ID，格式为 `source:key` |
| `title` | 内容标题 |
| `url` | 原始链接 |
| `duration_seconds` | 时长（秒），文本内容为 0 |
| `duration` | 人类可读时长，如 `03:04`、`3分18秒` |

## `item_id` 格式规范

```
source:unique_key
```

| 数据源 | unique_key 来源 | 示例 |
|--------|----------------|------|
| bilibili | BV 号 | `bilibili:BV1p1e26ZEXc` |
| xiaohongshu | note_id | `xhs:6ab4d1a1000000001303d31c` |
| memo | 文件夹-标题哈希 | `memo:学习笔记-abc123` |
| safari | URL 域名+路径哈希 | `safari:example.com-path` |

**要求**：
- 同一内容在不同场合必须有相同的 `item_id`
- 如果数据源本身没有唯一 ID，用 `url` 的哈希值生成
- 禁止使用自增整数或 UUID 作为 `item_id`

## 各数据源详情

### 1. Bilibili (`bilibili`)

**获取方式**：`bili hot -n 20 --json`

**特有字段**：
- `owner.name`: UP 主昵称
- `stats`: 包含 `liked_count`、`comment_count` 等

**示例**：
```json
{
  "source": "bilibili",
  "item_id": "bilibili:BV1p1e26ZEXc",
  "type": "video",
  "title": "爱，让豆包长出血肉",
  "url": "https://www.bilibili.com/video/BV1p1e26ZEXc",
  "content": "BGM：Be Okay 豆包沉默的几秒在想什么...",
  "duration_seconds": 140,
  "duration": "02:20",
  "owner": {"name": "虚构小郎君"},
  "stats": {"liked_count": 12345}
}
```

**限制**：
- 每次最多获取 20 条热门
- 不需要登录

### 2. 小红书 (`xiaohongshu`)

**获取方式**：`xhs hot -c <category> --json`

**特有字段**：
- `category`: 类别，如 `fashion`、`food`、`travel`
- `note_card.display_title`: 笔记标题
- `note_card.user.nick_name`: 作者昵称
- `note_card.interact_info.liked_count`: 点赞数
- `note_card.video.capa.duration`: 视频时长（秒），非视频笔记为 0

**示例**：
```json
{
  "source": "xiaohongshu",
  "item_id": "xhs:6ab4d1a1000000001303d31c",
  "type": "text",
  "title": "秋夜里这杯微醺，是枇杷和梨的味道",
  "url": "https://www.xiaohongshu.com/explore?note_id=6ab4d1a1000000001303d31c",
  "content": "秋夜里这杯微醺，是枇杷和梨的味道 | by 小噗 | 👍 233",
  "duration_seconds": 0,
  "duration": "",
  "category": "food"
}
```

**限制**：
- 类别包括：`fashion`、`food`、`travel`、`fitness`、`movie`、`career`、`love`、`home`、`gaming`、`cosmetics`
- 每次随机抽取 2 个类别以提升速度
- 非视频笔记 `duration_seconds` 为 0，在时长筛选时按文本处理

### 3. macOS 备忘录 (`memo`)

**获取方式**：`memo notes -nc`（`-nc` 绕过缓存）

**特有字段**：
- `folder`: 文件夹名称
- 无正文，只有标题

**示例**：
```json
{
  "source": "memo",
  "item_id": "memo:学习笔记-abc123",
  "type": "text",
  "title": "学习笔记 - Web3 与区块链基础",
  "url": "",
  "content": "学习笔记 - Web3 与区块链基础",
  "duration_seconds": 0,
  "duration": null,
  "folder": "学习笔记"
}
```

**限制**：
- 只能获取标题，无法直接获取完整备忘录正文
- 无 URL（因为是本地数据）
- `duration` 为 `null` 时表示无时长概念

### 4. Safari 书签 (`safari`)

**获取方式**：`safari-bookmarks list --format json`

**特有字段**：
- `url`: 书签 URL
- 可能包含文件夹层级信息

**示例**：
```json
{
  "source": "safari",
  "item_id": "safari:example.com-path",
  "type": "article",
  "title": "某篇文章标题",
  "url": "https://example.com/article",
  "content": "https://example.com/article",
  "duration_seconds": 0,
  "duration": null
}
```

**限制**：
- `safari-bookmarks list --json` 有编码 bug，使用 `--format json` 替代
- 无时长概念

## 时长处理规则

| `duration_seconds` | `duration` | 处理方式 |
|-------------------|-----------|---------|
| > 0 | `MM:SS` | 按视频处理，参与时长筛选 |
| 0 | `""` 或 `null` | 按文本处理，不参与时长筛选 |
| 缺失 | 缺失 | 按文本处理 |

## 去重逻辑

- 基于 `item_id` 去重
- `history` 记录所有已推荐过的 `item_id`
- `disliked` 记录用户点过"不喜欢"的 `item_id`
- 过滤时同时排除 `history` 和 `disliked` 中的内容
