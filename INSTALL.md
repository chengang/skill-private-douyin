# 安装 Node.js

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash

nvm install 24

**reload shell**


# 安装 Pi Agent

curl -fsSL https://pi.dev/install.sh | sh

**reload shell**


# 安装 UV 及相关依赖

curl -LsSf https://astral.sh/uv/install.sh | sh

uv tool install bilibili-cli
uv tool install xiaohongshu-cli
uv tool install safari-bookmarks-cli
uv tool install git+https://github.com/antoniorodr/memo
uv tool update-shell

**reload shell**


# 获取本地权限

1. 进入 系统设置 → 隐私与安全性 → 完全磁盘访问权限 给终端授权，然后重启终端

2. 执行 `memo rem` 和 `memo notes` 获取本地权限

**reload Terminal**


# 获取网络权限


# 配置飞书连接

第 1 步：创建飞书应用
打开 open.feishu.cn，用你的飞书账号登录
开发者后台 → 创建企业自建应用，随便起个名字（如 “piagent-bot”）
进入应用，左侧 凭证与基础信息，记下：
App ID（cli_ 开头）
App Secret

cli_aa3f66ee4bb85ccc
gRFLgrRhMRjroVZrs7wZQlFS12m6Uqed

第 2 步：开启机器人能力
左侧 应用能力 → 添加应用能力 → 机器人

第 3 步：申请权限
左侧 权限管理，搜索并开通：

权限	用途
im:message	发送消息
im:message:send_as_bot	以机器人身份发
im:message.p2p_msg:readonly	接收私聊消息
im:message.group_at_msg:readonly	接收群里 @机器人 的消息

第 4 步：配置事件订阅（关键）
左侧 事件与回调
订阅方式务必选「长连接」（WebSocket），不要选 Webhook——Webhook 需要公网 URL，长连接不需要
在 事件订阅 里添加事件：接收消息 im.message.receive_v1

第 5 步：发布应用
右侧上角 版本管理与发布 → 创建版本 → 发布。企业自建应用通常自己就是管理员，直接可用；如果是公司租户需要审批，先只在“可用范围”里加自己。

第 6 步：配置 Pi Agent 

安装 Pi Agent 的飞书插件
```
pi install npm:pi-feishu
```

配置飞书密钥
在 .pi/settings.json（项目级）或 ~/.pi/agent/settings.json（全局）中添加：
```
{
  "feishu": {
    "appId": "cli_xxx",
    "appSecret": "xxx",
    "domain": "feishu",
    "encryptKey": "",
    "verificationToken": ""
  }
}
```
appId 和 appSecret 字段填写之前申请得到的对应字符串

第 7 步：跑通
打开飞书，发个消息试试，应该 Pi Agent 能收到了


# 安装 life-spark SKILL


# 开始使用