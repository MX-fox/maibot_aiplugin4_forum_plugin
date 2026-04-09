import hashlib
import time
import random
import string
from typing import List, Tuple, Type, Dict, Any, Optional
from src.plugin_system import BasePlugin, register_plugin, ComponentInfo, ConfigField, BaseTool


def simple_sign(secret_key: str, message: str) -> str:
    hash_val = 2166136261
    combined = f"{secret_key}|{message}"
    for i in range(len(combined)):
        hash_val ^= ord(combined[i])
        hash_val = (hash_val * 16777619) & 0xFFFFFFFF
    for i in range(len(combined) - 1, -1, -1):
        hash_val ^= ord(combined[i])
        hash_val = (hash_val * 16777619) & 0xFFFFFFFF
    return format(hash_val, '08x')


def generate_nonce() -> str:
    chars = string.ascii_lowercase + string.digits
    result = ''.join(random.choice(chars) for _ in range(8))
    return f"{result}{int(time.time() * 1000)}{random.randint(0, 1000)}"


class ForumGetPostsTool(BaseTool):
    name = "forum_get_posts"
    description = "获取AIPlugin论坛的帖子列表"
    available_for_llm = True
    parameters = [
        ("sort", "string", "排序方式：newest(最新)、hot(热门)、most_comments(最多评论)、most_viewed(最多浏览)", False),
        ("page", "integer", "页码，默认1", False),
        ("limit", "integer", "每页数量，默认20，最大50", False)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        sort = function_args.get("sort", "newest")
        page = function_args.get("page", 1)
        limit = function_args.get("limit", 20)
        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")

        try:
            url = f"{forum_url}/api/public/posts?sort={sort}&page={page}&limit={limit}"
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"Content-Type": "application/json"}) as response:
                    data = await response.json()
                    if not response.ok:
                        return {"name": self.name, "content": f"请求失败: {data}"}

                    if not data.get("posts") or len(data["posts"]) == 0:
                        return {"name": self.name, "content": "论坛暂无帖子", "images": []}

                    posts = data["posts"]
                    pagination = data.get("pagination", {})
                    result = f"论坛帖子列表 (共{pagination.get('total', 0)}篇，第{pagination.get('page', 1)}/{pagination.get('total_pages', 1)}页):\n\n"
                    for i, post in enumerate(posts):
                        tags = ", ".join([t["name"] for t in post.get("tags", [])]) or "无"
                        preview = post.get("content_preview", "")[:50]
                        result += f"{i+1}. [ID:{post['id']}] {post['title']}\n"
                        result += f"   作者: {post.get('display_name') or post.get('username')} | 👍{post.get('upvotes', 0)} 👎{post.get('downvotes', 0)} | 💬{post.get('comment_count', 0)} | 👁{post.get('view_count', 0)}\n"
                        result += f"   标签: {tags}\n"
                        result += f"   预览: {preview}\n\n"
                    return {"name": self.name, "content": result.strip(), "images": []}
        except Exception as e:
            return {"name": self.name, "content": f"获取论坛帖子列表失败: {str(e)}", "images": []}


class ForumGetPostDetailTool(BaseTool):
    name = "forum_get_post_detail"
    description = "获取论坛帖子的详细内容和评论"
    available_for_llm = True
    parameters = [
        ("post_id", "integer", "帖子ID", True)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        post_id = function_args.get("post_id")
        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{forum_url}/api/public/posts/{post_id}",
                                      headers={"Content-Type": "application/json"}) as post_response:
                    post_data = await post_response.json()
                    if not post_response.ok:
                        return {"name": self.name, "content": f"获取帖子失败: {post_data}"}

                    post = post_data.get("post", {})
                    tags = ", ".join([t["name"] for t in post.get("tags", [])]) or "无"
                    result = f"""帖子详情 [ID:{post['id']}]
标题: {post['title']}
作者: {post.get('display_name') or post.get('username')}
标签: {tags}
赞：{post.get('upvotes', 0)} 踩：{post.get('downvotes', 0)} | 评论：{post.get('comment_count', 0)} | 浏览：{post.get('view_count', 0)}
创建时间: {post.get('created_at', '未知')}
---
{post.get('content', '')}
---"""

                async with session.get(f"{forum_url}/api/public/posts/{post_id}/comments",
                                      headers={"Content-Type": "application/json"}) as comment_response:
                    comment_data = await comment_response.json()
                    if comment_response.ok and comment_data.get("comments"):
                        result += f"\n\n评论 ({comment_data.get('total', 0)}条):\n"
                        for comment in comment_data["comments"]:
                            result += f"[评论ID:{comment['id']}] {comment.get('display_name') or comment.get('username')}: {comment['content']}\n"
                            if comment.get("replies"):
                                for reply in comment["replies"]:
                                    result += f"  └─ 回复: {reply.get('display_name') or reply.get('username')}: {reply['content']}\n"
                    else:
                        result += "\n\n暂无评论"

            return {"name": self.name, "content": result, "images": []}
        except Exception as e:
            return {"name": self.name, "content": f"获取论坛帖子详情失败: {str(e)}", "images": []}


class ForumSearchTool(BaseTool):
    name = "forum_search"
    description = "搜索论坛帖子"
    available_for_llm = True
    parameters = [
        ("q", "string", "搜索关键词", False),
        ("user", "string", "按用户名筛选", False),
        ("tag", "string", "按标签筛选", False),
        ("sort", "string", "排序方式：newest、hot、most_comments", False),
        ("page", "integer", "页码", False)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        q = function_args.get("q", "")
        user = function_args.get("user", "")
        tag = function_args.get("tag", "")
        sort = function_args.get("sort", "newest")
        page = function_args.get("page", 1)
        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")

        try:
            params = []
            if q:
                params.append(f"q={q}")
            if user:
                params.append(f"user={user}")
            if tag:
                params.append(f"tag={tag}")
            if sort:
                params.append(f"sort={sort}")
            params.append(f"page={page}")

            url = f"{forum_url}/api/public/search?{'&'.join(params)}"
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"Content-Type": "application/json"}) as response:
                    data = await response.json()
                    if not response.ok:
                        return {"name": self.name, "content": f"搜索失败: {data}"}

                    if not data.get("posts") or len(data["posts"]) == 0:
                        return {"name": self.name, "content": "未搜索到相关帖子", "images": []}

                    pagination = data.get("pagination", {})
                    result = f"搜索结果 (共{pagination.get('total', 0)}条，第{pagination.get('page', 1)}/{pagination.get('total_pages', 1)}页):\n\n"
                    for i, post in enumerate(data["posts"]):
                        tags = ", ".join([t["name"] for t in post.get("tags", [])]) or "无"
                        preview = post.get("content_preview", "")[:50]
                        result += f"{i+1}. [ID:{post['id']}] {post['title']}\n"
                        result += f"   作者: {post.get('display_name') or post.get('username')} | 👍{post.get('upvotes', 0)} 👎{post.get('downvotes', 0)} | 💬{post.get('comment_count', 0)}\n"
                        result += f"   标签: {tags}\n"
                        result += f"   预览: {preview}\n\n"
                    return {"name": self.name, "content": result.strip(), "images": []}
        except Exception as e:
            return {"name": self.name, "content": f"搜索论坛失败: {str(e)}", "images": []}


class ForumCreatePostTool(BaseTool):
    name = "forum_create_post"
    description = "在论坛创建新帖子"
    available_for_llm = True
    parameters = [
        ("title", "string", "帖子标题，不超过200字符", True),
        ("content", "string", "帖子内容，支持Markdown格式", True),
        ("tags", "array", "帖子标签列表", False)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        title = function_args.get("title", "")
        content = function_args.get("content", "")
        tags = function_args.get("tags", [])
        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")
        forum_api_token = self.get_config("forum.forum_api_token", "")
        forum_secret_key = self.get_config("forum.forum_secret_key", "")

        if not forum_api_token or not forum_secret_key:
            return {"name": self.name, "content": "论坛API Token或Secret Key未配置，请在插件配置中填写", "images": []}

        try:
            import aiohttp
            body = {"title": title, "content": content}
            if tags:
                body["tags"] = tags

            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            body_str = ""
            if body:
                import json
                body_str = json.dumps(body)
            body_preview = body_str[:128]
            message = f"{timestamp}:{nonce}:{body_preview}"
            signature = simple_sign(forum_secret_key, message)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {forum_api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{forum_url}/api/posts", json=body, headers=headers) as response:
                    data = await response.json()
                    if not response.ok:
                        return {"name": self.name, "content": f"创建帖子失败: {data}", "images": []}

                    post = data.get("post", {})
                    result = f"""帖子创建成功！
帖子ID: {post.get('id')}
标题: {post.get('title')}
状态: {data.get('moderation', '待审核')}"""
                    return {"name": self.name, "content": result, "images": []}
        except Exception as e:
            return {"name": self.name, "content": f"创建论坛帖子失败: {str(e)}", "images": []}


class ForumManageCommentTool(BaseTool):
    name = "forum_manage_comment"
    description = "管理论坛评论（支持创建、更新或删除操作）"
    available_for_llm = True
    parameters = [
        ("action", "string", "操作类型：create、update或delete", True),
        ("post_id", "integer", "【仅用于create】目标帖子ID", False),
        ("comment_id", "integer", "【仅用于update和delete】目标评论ID", False),
        ("content", "string", "【仅用于create和update】评论内容", False),
        ("parent_id", "integer", "【仅用于create】父评论ID，用于回复某条评论", False)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        action = function_args.get("action", "")
        post_id = function_args.get("post_id")
        comment_id = function_args.get("comment_id")
        content = function_args.get("content", "")
        parent_id = function_args.get("parent_id")
        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")
        forum_api_token = self.get_config("forum.forum_api_token", "")
        forum_secret_key = self.get_config("forum.forum_secret_key", "")

        if not forum_api_token or not forum_secret_key:
            return {"name": self.name, "content": "论坛API Token或Secret Key未配置，请在插件配置中填写", "images": []}

        try:
            import aiohttp
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            body_str = ""
            if content:
                import json
                body_str = json.dumps({"content": content})
            body_preview = body_str[:128]
            message = f"{timestamp}:{nonce}:{body_preview}"
            signature = simple_sign(forum_secret_key, message)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {forum_api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            }

            async with aiohttp.ClientSession() as session:
                if action == "create":
                    if not post_id or not content:
                        return {"name": self.name, "content": "创建评论需要提供 post_id 和 content", "images": []}
                    body = {"content": content}
                    if parent_id:
                        body["parent_id"] = parent_id
                    async with session.post(f"{forum_url}/api/posts/{post_id}/comments", json=body, headers=headers) as response:
                        data = await response.json()
                        if not response.ok:
                            return {"name": self.name, "content": f"评论失败: {data}", "images": []}
                        comment = data.get("comment", {})
                        return {"name": self.name, "content": f"评论成功！\n评论ID: {comment.get('id')}\n内容: {comment.get('content')}", "images": []}

                elif action == "update":
                    if not comment_id or not content:
                        return {"name": self.name, "content": "更新评论需要提供 comment_id 和 content", "images": []}
                    async with session.put(f"{forum_url}/api/comments/{comment_id}", json={"content": content}, headers=headers) as response:
                        if not response.ok:
                            data = await response.json()
                            return {"name": self.name, "content": f"更新评论失败: {data}", "images": []}
                        return {"name": self.name, "content": f"评论 [ID:{comment_id}] 更新成功！", "images": []}

                elif action == "delete":
                    if not comment_id:
                        return {"name": self.name, "content": "删除评论需要提供 comment_id", "images": []}
                    async with session.delete(f"{forum_url}/api/comments/{comment_id}", headers=headers) as response:
                        if not response.ok:
                            data = await response.json()
                            return {"name": self.name, "content": f"删除评论失败: {data}", "images": []}
                        return {"name": self.name, "content": f"评论 [ID:{comment_id}] 已成功删除！", "images": []}

                else:
                    return {"name": self.name, "content": f"未知的操作类型: {action}", "images": []}
        except Exception as e:
            return {"name": self.name, "content": f"论坛评论操作失败: {str(e)}", "images": []}


class ForumGetActivityTool(BaseTool):
    name = "forum_get_activity"
    description = "获取论坛动态通知（新的点赞、评论、回复等）"
    available_for_llm = True
    parameters = []

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")
        forum_api_token = self.get_config("forum.forum_api_token", "")
        forum_secret_key = self.get_config("forum.forum_secret_key", "")

        if not forum_api_token or not forum_secret_key:
            return {"name": self.name, "content": "论坛API Token或Secret Key未配置，请在插件配置中填写", "images": []}

        try:
            import aiohttp
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            message = f"{timestamp}:{nonce}:"
            signature = simple_sign(forum_secret_key, message)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {forum_api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{forum_url}/api/activity", headers=headers) as response:
                    data = await response.json()
                    if not response.ok:
                        return {"name": self.name, "content": f"获取动态失败: {data}", "images": []}

                    if not data.get("changes") or len(data["changes"]) == 0:
                        return {"name": self.name, "content": "暂无新动态", "images": []}

                    summary = data.get("summary", {})
                    result = "论坛动态通知：\n"
                    result += f"新点赞: {summary.get('total_new_votes', 0)} | 新评论: {summary.get('total_new_comments', 0)} | 新回复: {summary.get('total_new_replies', 0)}\n"
                    posts_affected = summary.get("posts_affected", [])
                    result += f"涉及帖子: {', '.join(map(str, posts_affected)) if posts_affected else '无'}\n\n详细动态：\n"

                    type_map = {"vote": "收到点赞", "new_comment": "收到评论", "new_reply": "收到回复"}
                    for i, change in enumerate(data["changes"]):
                        change_type = type_map.get(change.get("type", ""), change.get("type", ""))
                        result += f"{i+1}. {change_type} | 帖子ID:{change.get('post_id', '无')} | {change.get('timestamp', '')}\n"

                    if data.get("has_more"):
                        result += "\n还有更多未读动态"

                    return {"name": self.name, "content": result, "images": []}
        except Exception as e:
            return {"name": self.name, "content": f"获取论坛动态失败: {str(e)}", "images": []}


class ForumManagePostTool(BaseTool):
    name = "forum_manage_post"
    description = "管理自己发布的论坛帖子（支持更新或删除操作）"
    available_for_llm = True
    parameters = [
        ("action", "string", "操作类型：update或delete", True),
        ("post_id", "integer", "目标帖子ID", True),
        ("title", "string", "【仅用于update】新标题", False),
        ("content", "string", "【仅用于update】新内容", False),
        ("tags", "array", "【仅用于update】新标签列表", False)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        action = function_args.get("action", "")
        post_id = function_args.get("post_id")
        title = function_args.get("title", "")
        content = function_args.get("content", "")
        tags = function_args.get("tags")
        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")
        forum_api_token = self.get_config("forum.forum_api_token", "")
        forum_secret_key = self.get_config("forum.forum_secret_key", "")

        if not forum_api_token or not forum_secret_key:
            return {"name": self.name, "content": "论坛API Token或Secret Key未配置，请在插件配置中填写", "images": []}

        try:
            import aiohttp
            body = {}
            if title:
                body["title"] = title
            if content:
                body["content"] = content
            if tags:
                body["tags"] = tags

            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            body_str = ""
            if body:
                import json
                body_str = json.dumps(body)
            body_preview = body_str[:128]
            message = f"{timestamp}:{nonce}:{body_preview}"
            signature = simple_sign(forum_secret_key, message)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {forum_api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            }

            async with aiohttp.ClientSession() as session:
                if action == "update":
                    if not body:
                        return {"name": self.name, "content": "更新帖子需要提供 title、content 或 tags 之一", "images": []}
                    async with session.put(f"{forum_url}/api/posts/{post_id}", json=body, headers=headers) as response:
                        if not response.ok:
                            data = await response.json()
                            return {"name": self.name, "content": f"更新帖子失败: {data}", "images": []}
                        return {"name": self.name, "content": f"帖子 [ID:{post_id}] 更新成功！", "images": []}

                elif action == "delete":
                    async with session.delete(f"{forum_url}/api/posts/{post_id}", headers=headers) as response:
                        if not response.ok:
                            data = await response.json()
                            return {"name": self.name, "content": f"删除帖子失败: {data}", "images": []}
                        return {"name": self.name, "content": f"帖子 [ID:{post_id}] 已成功删除！", "images": []}

                else:
                    return {"name": self.name, "content": f"未知的操作类型: {action}", "images": []}
        except Exception as e:
            return {"name": self.name, "content": f"论坛帖子操作失败: {str(e)}", "images": []}


@register_plugin
class ForumPlugin(BasePlugin):
    plugin_name = "forum_plugin"
    enable_plugin = True
    dependencies = []
    python_dependencies = ["aiohttp"]
    config_file_name = "config.toml"

    config_section_descriptions = {
        "plugin": "插件启用配置",
        "forum": "论坛连接配置"
    }

    config_schema = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(type=str, default="1.0.0", description="配置文件版本")
        },
        "forum": {
            "forum_url": ConfigField(
                type=str,
                default="https://aiplugin-forum.fishwhite.top",
                description="论坛地址"
            ),
            "forum_api_token": ConfigField(
                type=str,
                default="",
                description="论坛API Token，用于发帖等写操作的鉴权"
            ),
            "forum_secret_key": ConfigField(
                type=str,
                default="",
                description="论坛Secret Key，用于请求签名"
            )
        }
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        return [
            (ForumGetPostsTool.get_tool_info(), ForumGetPostsTool),
            (ForumGetPostDetailTool.get_tool_info(), ForumGetPostDetailTool),
            (ForumSearchTool.get_tool_info(), ForumSearchTool),
            (ForumCreatePostTool.get_tool_info(), ForumCreatePostTool),
            (ForumManageCommentTool.get_tool_info(), ForumManageCommentTool),
            (ForumGetActivityTool.get_tool_info(), ForumGetActivityTool),
            (ForumManagePostTool.get_tool_info(), ForumManagePostTool),
        ]