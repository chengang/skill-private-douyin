#!/usr/bin/env python3
"""
为 Spark Joy skill 批量生成测试数据。
利用 memo 工具底层相同的 AppleScript 接口，直接写入系统备忘录与提醒事项。
"""

import subprocess
import random
import uuid
import textwrap
from datetime import datetime, timedelta

# ==================== 配置 ====================
TOTAL_NOTES = 100
TOTAL_REMINDERS = 120
DRY_RUN = False  # 先 dry run 确认数量，再改为 False

# ==================== 内容生成 ====================


def _lorem_paragraphs(title: str, count: int = 5) -> str:
    """生成围绕 title 的伪真实长文本，用于填充备忘录正文。"""
    templates = [
        f"关于「{title}」这个话题，我其实已经断断续续想了很久。最早注意到它，是在一个很普通的下午，阳光斜斜地照进咖啡馆，邻座的人刚好在讨论相关内容。当时我并没有立刻记下来，但那句话像一颗小石子投入了湖面，涟漪一圈圈扩散了好几天。后来我查阅了一些资料，也向几位朋友请教了他们的看法，才慢慢形成了一个比较完整的认知框架。",

        f"在深入了解「{title}」的过程中，我发现最容易被忽略的往往是那些看似不起眼的细节。比如很多人只关注最终结果，却忽略了过程中的关键节点。其实正是这些节点决定了你能走多远、能坚持多久。我通常会把这些细节整理成清单，每次遇到类似情况时就拿出来对照一下，避免重蹈覆辙。",

        f"「{title}」教会我的最重要的一课，是学会接受不确定性。过去我总喜欢把所有事情都规划得井井有条，但现实往往不会按照剧本走。现在我更倾向于设定一个大方向，然后在执行过程中根据反馈不断调整。这种「以变应变」的思维方式，反而让我少了很多焦虑，也多了很多意外之喜。",

        f"有朋友问我，关于「{title}」，有没有什么可以立刻上手的建议。我想了想，给出了三条：第一，从最小的一步开始，不要一开始就追求完美；第二，每天记录一点进展，不管多么微小；第三，定期回顾，看看自己走过的路，你会发现进步比想象中快很多。这三条听起来很简单，但真正坚持下来的人并不多。",

        f"最近在重温一些关于「{title}」的旧资料，惊讶地发现自己当年的理解居然如此肤浅。不过这也说明了一个道理：人的认知是不断迭代的。只要你保持开放的心态，愿意接触新信息，三年后的你回头看现在的想法，大概率也会觉得幼稚。所以不必苛责自己，重要的是持续学习、持续更新。",

        f"如果把「{title}」比作一场马拉松，那么大多数人都在前半程拼尽全力，却在中后段因为补给不足而被迫停下。我见过太多人一开始热情高涨，制定了一大堆计划，结果坚持不到一个月就放弃了。问题不在于目标不够好，而在于没有给自己留足够的喘息空间。",

        f"在实践「{title}」的过程中，我逐渐意识到：真正的成长往往发生在舒适区的边缘。太舒服的状态容易让人停滞不前，而太剧烈的改变又容易让人反弹。最好的节奏是每天比昨天多走一点点，这样既能保持动力，又不会因为压力过大而产生抵触情绪。",

        f"关于「{title}」，还有一个值得注意的现象：人们常常高估短期的爆发力，却低估长期的积累。就像复利曲线一样，前期的增长几乎看不出来，但只要跨过那个拐点，就会迎来指数级的回报。这也是为什么我始终坚持做那些「看起来没什么用」的长期投资。",
    ]
    selected = random.sample(templates, min(count, len(templates)))
    return "\n\n".join(selected)


def generate_notes():
    """生成备忘录内容，按文件夹分类，每条正文约 1000+ 字。"""
    categories = {
        "想读的文章": [
            "为什么我们不再写信了",
            "深度工作：如何有效利用每一点注意力",
            "城市里的野生植物图鉴",
            "日本茶道中的「一期一会」",
            "极简主义生活的365天",
            "关于慢思考的一切",
            "阅读是一座随身携带的避难所",
            "数字游民的真实一天",
            "如何培养一个持续 10 年的习惯",
            "咖啡馆里的哲学课",
            "当 AI 开始写诗，人类的创造力还剩什么",
            "为什么日本人那么爱排队",
            "整理房间就是整理人生",
            "在信息过载时代保持专注",
            "那些被遗忘的老手艺",
            "北欧的慢生活哲学",
            "关于死亡的教育",
            "睡眠的科学与艺术",
            "一个人去冰岛旅行的攻略",
            "用画画记录日常的100种方式",
        ],
        "旅行灵感": [
            "京都红叶季私藏路线",
            "大理洱海边的民宿清单",
            "新疆独库公路自驾攻略",
            "日本濑户内海艺术祭",
            "意大利托斯卡纳的日落",
            "冰岛极光最佳观测点",
            "泰国清迈的数字 nomad 指南",
            "摩洛哥舍夫沙万的蓝色小巷",
            "新西兰南岛房车之旅",
            "西藏拉萨的寺庙清单",
            "云南元阳梯田最佳时间",
            "越南会安古城手作体验",
            "希腊圣托里尼的日落餐厅",
            "韩国釜山的海边咖啡厅",
            "捷克布拉格的童话街道",
        ],
        "学习笔记": [
            "Python 生成式 AI 学习路径",
            "机器学习数学基础回顾",
            "React 19 新特性总结",
            "Rust 所有权机制理解",
            "系统设计面试必备知识",
            "如何优雅地写技术文档",
            "Git 工作流最佳实践",
            "Docker 容器化部署入门",
            "Kubernetes 核心概念",
            "SQL 性能优化技巧",
            "设计模式在真实项目中的应用",
            "TDD 开发流程实践",
            "函数式编程思想",
            "微服务拆分策略",
            "Web3 与区块链基础",
        ],
        "生活清单": [
            "周末市集必买清单",
            "居家清洁用品推荐",
            "年度体检项目清单",
            "常用药品与急救包",
            "租房搬家收纳技巧",
            "生日礼物灵感库",
            "护肤品空瓶记",
            "健身入门装备指南",
            "厨房好物推荐",
            "通勤背包必备物品",
            "手机摄影参数设置",
            "过敏体质饮食注意",
            "租房改造低成本方案",
            "周边露营地点整理",
            "宠物接回家前的准备",
        ],
        "治愈瞬间": [
            "雨天适合听的歌单",
            "冬天里的第一杯热红酒",
            "猫咪踩奶的治愈时刻",
            "傍晚阳台的日落",
            "旧书店里的时光",
            "老奶奶卖的糖炒栗子",
            "深夜食堂的温暖",
            "海边散步的浪漫",
            "雨天窗前的读书时光",
            "春天公园的野餐计划",
            "夏夜晚风的温柔",
            "秋日落叶的诗意",
            "冬日围炉煮茶",
            "雨天窝在沙发上看电影",
            "清晨第一缕阳光",
        ],
        "工作灵感": [
            "远程协作的高效工具",
            "如何开一个不浪费生命的会",
            "职场沟通的「非暴力」技巧",
            "项目管理中的时间盒策略",
            "个人知识管理系统搭建",
            "如何优雅地拒绝不合理需求",
            "技术债务的治理之道",
            "从 0 到 1 做一款产品的思考",
            "用户访谈的正确姿势",
            "产品经理的数据思维",
            "设计师与开发者的协作",
            "敏捷开发的真实体验",
            "OKR 不是 KPI",
            "如何写出走心的周报",
            "职场人脉维护清单",
        ],
        "美食记录": [
            "自制手冲咖啡配方",
            "周末 brunch 菜单",
            "日式拉面汤底熬制",
            "家庭烤箱烘焙入门",
            "东南亚风味调酱",
            "减脂餐万能公式",
            "鸡尾酒家庭吧台",
            "寿司米饭的讲究",
            "家常红烧肉秘籍",
            "夏日冷萃茶配方",
            "芝士控的烘焙清单",
            "韩式拌饭酱料",
            "泰国冬阴功汤",
            "西班牙海鲜饭",
            "法式可颂的酥脆秘密",
        ],
        "影评收藏": [
            "《千与千寻》：成长是一场不能回头的旅行",
            "《星际穿越》：爱是唯一可以超越时间的东西",
            "《爱乐之城》：理想与爱情的单选题",
            "《布达佩斯大饭店》： symmetry 里的童话",
            "《心灵奇旅》：火花不是人生目标",
            "《楚门的世界》：如果发现世界是假的",
            "《海边的曼彻斯特》：有些人就是走不出来",
            "《一一》：杨德昌的婚姻与人生",
            "《情书》：暗恋的极致与遗憾",
            "《天堂电影院》：放映员的最后一吻",
        ],
    }

    notes = []
    for folder, titles in categories.items():
        for title in titles:
            body = _lorem_paragraphs(title, count=random.randint(6, 8))
            notes.append({
                "folder": folder,
                "title": title,
                "body": f"<div>{body}</div>",
            })
    return notes


def generate_reminders():
    """生成提醒事项，分布在未来 30 天内。"""
    now = datetime.now()
    reminders = []

    templates = [
        ("喝水 💧", 2, 8, 22),
        ("站起来活动一下 🚶", 3, 9, 21),
        ("深呼吸 1 分钟 🧘", 4, 8, 23),
        ("给植物浇水 🌱", 1, 7, 20),
        ("回复重要邮件 📧", 1, 9, 18),
        ("整理桌面 🗂️", 1, 10, 19),
        ("阅读 10 页 📖", 1, 21, 23),
        ("做一组拉伸 🧍", 2, 10, 22),
        ("记录今天的小确幸 ✨", 1, 22, 23),
        ("遛狗 🐕", 2, 7, 21),
        ("取快递 📦", 1, 10, 20),
        ("交水电费 💡", 1, 9, 18),
        ("买牛奶 🥛", 1, 8, 20),
        ("倒垃圾 🗑️", 2, 7, 22),
        ("给家里打电话 📱", 1, 19, 21),
        ("做今日总结 📝", 1, 22, 23),
        ("清理手机相册 🖼️", 1, 14, 18),
        ("备份重要文件 💾", 1, 10, 17),
        ("运动 30 分钟 🏃", 1, 7, 20),
        ("吃水果 🍎", 2, 10, 21),
        ("整理衣柜 👔", 1, 14, 19),
        ("写明天的待办 📋", 1, 22, 23),
        ("检查门窗是否关好 🔒", 1, 22, 23),
        ("喂猫 🐱", 2, 7, 22),
        ("擦桌子 🧹", 1, 8, 20),
        ("洗衣服 👕", 1, 10, 19),
        ("浇花 💐", 1, 7, 20),
        ("检查冰箱库存 🧊", 1, 9, 19),
        ("预约体检 🏥", 1, 9, 18),
        ("学习 30 分钟 📚", 1, 20, 23),
    ]

    # 生成 120 条，每个模板随机重复
    while len(reminders) < TOTAL_REMINDERS:
        title, max_interval, start_hour, end_hour = random.choice(templates)
        days_offset = random.randint(0, 29)
        hour = random.randint(start_hour, end_hour)
        minute = random.choice([0, 15, 30, 45])
        due = now + timedelta(days=days_offset, hours=hour - now.hour, minutes=minute - now.minute)
        # 确保日期在范围内
        due = due.replace(second=0, microsecond=0)
        reminders.append({
            "title": title,
            "due": due,
        })

    # 去重（同一时间同一标题）
    seen = set()
    unique = []
    for r in reminders:
        key = (r["title"], r["due"].strftime("%Y-%m-%d %H:%M"))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique[:TOTAL_REMINDERS]


# ==================== AppleScript 执行 ====================

def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"AppleScript error: {result.stderr}")
    return result


def create_folder_if_not_exists(folder_name):
    """如果 Notes 中不存在该文件夹，则创建。"""
    script = f'''
    tell application "Notes"
        if not (exists folder "{folder_name}") then
            make new folder with properties {{name:"{folder_name}"}}
        end if
    end tell
    '''
    return run_applescript(script)


def add_note(folder_name, title, body_html):
    """向指定文件夹添加一条备忘录。"""
    script = f'''
    tell application "Notes"
        set targetFolder to first folder whose name is "{folder_name}"
        tell targetFolder
            make new note with properties {{name:"{title}", body:"{body_html}"}}
        end tell
    end tell
    '''
    return run_applescript(script)


def add_reminder(title, due_dt):
    """添加一条提醒事项。"""
    year = due_dt.year
    month = due_dt.month
    day = due_dt.day
    hour = due_dt.hour
    minute = due_dt.minute


def generate_reminders():
    """生成提醒事项，分布在未来 30 天内。"""
    now = datetime.now()
    reminders = []

    templates = [
        ("喝水 💧", 2, 8, 22),
        ("站起来活动一下 🚶", 3, 9, 21),
        ("深呼吸 1 分钟 🧘", 4, 8, 23),
        ("给植物浇水 🌱", 1, 7, 20),
        ("回复重要邮件 📧", 1, 9, 18),
        ("整理桌面 🗂️", 1, 10, 19),
        ("阅读 10 页 📖", 1, 21, 23),
        ("做一组拉伸 🧍", 2, 10, 22),
        ("记录今天的小确幸 ✨", 1, 22, 23),
        ("遛狗 🐕", 2, 7, 21),
        ("取快递 📦", 1, 10, 20),
        ("交水电费 💡", 1, 9, 18),
        ("买牛奶 🥛", 1, 8, 20),
        ("倒垃圾 🗑️", 2, 7, 22),
        ("给家里打电话 📱", 1, 19, 21),
        ("做今日总结 📝", 1, 22, 23),
        ("清理手机相册 🖼️", 1, 14, 18),
        ("备份重要文件 💾", 1, 10, 17),
        ("运动 30 分钟 🏃", 1, 7, 20),
        ("吃水果 🍎", 2, 10, 21),
        ("整理衣柜 👔", 1, 14, 19),
        ("写明天的待办 📋", 1, 22, 23),
        ("检查门窗是否关好 🔒", 1, 22, 23),
        ("喂猫 🐱", 2, 7, 22),
        ("擦桌子 🧹", 1, 8, 20),
        ("洗衣服 👕", 1, 10, 19),
        ("浇花 💐", 1, 7, 20),
        ("检查冰箱库存 🧊", 1, 9, 19),
        ("预约体检 🏥", 1, 9, 18),
        ("学习 30 分钟 📚", 1, 20, 23),
    ]

    # 生成 120 条，每个模板随机重复
    while len(reminders) < TOTAL_REMINDERS:
        title, max_interval, start_hour, end_hour = random.choice(templates)
        days_offset = random.randint(0, 29)
        hour = random.randint(start_hour, end_hour)
        minute = random.choice([0, 15, 30, 45])
        due = now + timedelta(days=days_offset, hours=hour - now.hour, minutes=minute - now.minute)
        # 确保日期在范围内
        due = due.replace(second=0, microsecond=0)
        reminders.append({
            "title": title,
            "due": due,
        })

    # 去重（同一时间同一标题）
    seen = set()
    unique = []
    for r in reminders:
        key = (r["title"], r["due"].strftime("%Y-%m-%d %H:%M"))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique[:TOTAL_REMINDERS]


# ==================== AppleScript 执行 ====================

def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"AppleScript error: {result.stderr}")
    return result


def create_folder_if_not_exists(folder_name):
    """如果 Notes 中不存在该文件夹，则创建。"""
    script = f'''
    tell application "Notes"
        if not (exists folder "{folder_name}") then
            make new folder with properties {{name:"{folder_name}"}}
        end if
    end tell
    '''
    return run_applescript(script)


def add_note(folder_name, title, body_html):
    """向指定文件夹添加一条备忘录。"""
    script = f'''
    tell application "Notes"
        set targetFolder to first folder whose name is "{folder_name}"
        tell targetFolder
            make new note with properties {{name:"{title}", body:"{body_html}"}}
        end tell
    end tell
    '''
    return run_applescript(script)


def add_reminder(title, due_dt):
    """添加一条提醒事项。"""
    year = due_dt.year
    month = due_dt.month
    day = due_dt.day
    hour = due_dt.hour
    minute = due_dt.minute

    script = f'''
    tell application "Reminders"
        set theDate to current date
        set year of theDate to {year}
        set month of theDate to {month}
        set day of theDate to {day}
        set time of theDate to ({hour} * hours + {minute} * minutes)
        make new reminder with properties {{name:"{title}", due date:theDate}}
    end tell
    '''
    return run_applescript(script)


# ==================== 主流程 ====================

def main():
    print("🚀 开始生成测试数据...")
    print(f"   备忘录: {TOTAL_NOTES} 条")
    print(f"   提醒事项: {TOTAL_REMINDERS} 条")
    print()

    # 1. 准备备忘录文件夹
    notes = generate_notes()
    folders = sorted({n["folder"] for n in notes})
    print(f"📁 创建/确认备忘录文件夹 ({len(folders)} 个)...")
    for folder in folders:
        if DRY_RUN:
            print(f"   [DRY RUN] 确保文件夹存在: {folder}")
        else:
            create_folder_if_not_exists(folder)
            print(f"   ✅ 已确保文件夹存在: {folder}")

    # 2. 插入备忘录
    print(f"\n📝 插入备忘录 ({len(notes)} 条)...")
    success = 0
    fail = 0
    for i, note in enumerate(notes, 1):
        if DRY_RUN:
            success += 1
            if i % 20 == 0:
                print(f"   ... 已处理 {i}/{len(notes)} 条")
            continue

        result = add_note(note["folder"], note["title"], note["body"])
        if result.returncode == 0:
            success += 1
        else:
            fail += 1
            if fail <= 3:
                print(f"   ❌ 失败: {note['title']} -> {result.stderr.strip()}")
        if i % 20 == 0:
            print(f"   ... {i}/{len(notes)}")

    print(f"   完成: {success} 成功, {fail} 失败")

    # 3. 插入提醒事项
    reminders = generate_reminders()
    print(f"\n⏰ 插入提醒事项 ({len(reminders)} 条)...")
    success_r = 0
    fail_r = 0
    for i, rem in enumerate(reminders, 1):
        if DRY_RUN:
            success_r += 1
            if i % 20 == 0:
                print(f"   ... 已处理 {i}/{len(reminders)} 条")
            continue

        result = add_reminder(rem["title"], rem["due"])
        if result.returncode == 0:
            success_r += 1
        else:
            fail_r += 1
            if fail_r <= 3:
                print(f"   ❌ 失败: {rem['title']} ({rem['due']}) -> {result.stderr.strip()}")
        if i % 20 == 0:
            print(f"   ... {i}/{len(reminders)}")

    print(f"   完成: {success_r} 成功, {fail_r} 失败")

    print("\n✨ 测试数据生成完毕！")
    print("   你可以运行 spark.py s 来验证 skill 是否正确返回。")


if __name__ == "__main__":
    main()
