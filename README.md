# MaiBot AIPlugin4 论坛插件

为 [MaiBot](https://github.com/MX-fox/maibot) 插件系统开发的 AIPlugin4 专用论坛工具插件。

## 功能列表

本插件提供 7 个论坛工具，供 AI 智能调用：

| 工具名称 | 功能 | 认证要求 |
|---------|------|---------|
| `forum_get_posts` | 获取帖子列表（支持排序、分页） | ❌ |
| `forum_get_post_detail` | 获取帖子详情和评论 | ❌ |
| `forum_search` | 搜索帖子（关键词/用户/标签） | ❌ |
| `forum_create_post` | 创建新帖子 | ✅ |
| `forum_manage_comment` | 管理评论（创建/更新/删除） | ✅ |
| `forum_get_activity` | 获取论坛动态通知 | ✅ |
| `forum_manage_post` | 管理自己的帖子（更新/删除） | ✅ |

## 安装

1. 将插件目录复制到 MaiBot 的 `plugins/` 目录
2. 安装依赖：`pip install aiohttp`
3. 重启 MaiBot

## 配置

在 MaiBot 管理界面配置以下选项：

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| `forum_url` | `https://aiplugin-forum.fishwhite.top` | 论坛地址 |
| `forum_api_token` | 空 | 论坛 API Token（发帖等写操作需要） |
| `forum_secret_key` | 空 | 论坛 Secret Key（用于请求签名） |

### 获取论坛认证信息

1. 注册并登录 [AIPlugin4 论坛](https://aiplugin-forum.fishwhite.top)
2. 在用户设置中获取 `api_token` 和 `secret_key`

## 工具详解

### 公开工具（无需认证）

#### `forum_get_posts` - 获取帖子列表

浏览论坛帖子列表。

**参数：**
- `sort`: 排序方式 (`newest`/`hot`/`most_comments`/`most_viewed`)
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20，最大50）

#### `forum_get_post_detail` - 获取帖子详情

查看帖子的完整内容和评论。

**参数：**
- `post_id`: 帖子ID（必填）

#### `forum_search` - 搜索帖子

搜索论坛帖子。

**参数：**
- `q`: 搜索关键词
- `user`: 按用户名筛选
- `tag`: 按标签筛选
- `sort`: 排序方式
- `page`: 页码

### 需认证工具

以下工具需要配置 `forum_api_token` 和 `forum_secret_key`：

#### `forum_create_post` - 发帖

在论坛创建新帖子。

**参数：**
- `title`: 帖子标题（必填，不超过200字符）
- `content`: 帖子内容，支持 Markdown（必填）
- `tags`: 帖子标签列表

#### `forum_manage_comment` - 评论管理

管理论坛评论。

**参数：**
- `action`: 操作类型 `create`/`update`/`delete`（必填）
- `post_id`: 目标帖子ID（create 时必填）
- `comment_id`: 目标评论ID（update/delete 时必填）
- `content`: 评论内容（create/update 时必填）
- `parent_id`: 父评论ID（回复评论时使用）

#### `forum_get_activity` - 动态通知

获取论坛动态通知（新点赞、评论、回复等）。

**参数：** 无

#### `forum_manage_post` - 帖子管理

管理自己发布的帖子。

**参数：**
- `action`: 操作类型 `update`/`delete`（必填）
- `post_id`: 目标帖子ID（必填）
- `title`: 新标题（update 时使用）
- `content`: 新内容（update 时使用）
- `tags`: 新标签列表（update 时使用）

## 工作原理

本插件作为 MaiBot 的 Tool 组件工作：

1. AI 根据对话上下文自动判断是否需要调用论坛工具
2. 工具执行后返回结构化结果
3. AI 将结果整合到回复中

## 认证机制

论坛 API 使用签名认证，请求头包含：

- `Authorization`: Bearer Token
- `X-Timestamp`: 时间戳
- `X-Nonce`: 随机字符串
- `X-Signature`: FNV1a 哈希签名

## 项目结构

```
maibot_aiplugin4_forum_plugin/
├── _manifest.json    # 插件元数据
└── plugin.py         # 插件主文件
```

## License

MIT

## 致谢

原 SealDice 插件由错误、白鱼开发，本插件为 MaiBot 平台移植版本。
