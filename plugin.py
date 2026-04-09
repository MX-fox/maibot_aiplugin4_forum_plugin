import asyncio
import json
import logging
import time
import random
import string
from typing import List, Tuple, Type, Dict, Any, Optional

import aiohttp

from src.plugin_system import BasePlugin, register_plugin, ComponentInfo, ConfigField, BaseTool, BaseCommand, ToolParamType

logger = logging.getLogger("forum_plugin")

API_PATHS = {
    "public_posts": "/api/public/posts",
    "public_post_detail": "/api/public/posts/{post_id}",
    "public_comments": "/api/public/posts/{post_id}/comments",
    "public_search": "/api/public/search",
    "posts": "/api/posts",
    "post_detail": "/api/posts/{post_id}",
    "comments": "/api/posts/{post_id}/comments",
    "comment_detail": "/api/comments/{comment_id}",
    "activity": "/api/activity",
}

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=10)


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


def validate_title(title: str) -> Tuple[bool, str]:
    if not title:
        return False, "标题不能为空"
    if len(title) > 200:
        return False, "标题不能超过200字符"
    return True, ""


def validate_content(content: str) -> Tuple[bool, str]:
    if not content:
        return False, "内容不能为空"
    if len(content) > 50000:
        return False, "内容不能超过50000字符"
    return True, ""


class ForumBaseTool(BaseTool):
    _forum_url: Optional[str] = None
    _forum_api_token: Optional[str] = None
    _forum_secret_key: Optional[str] = None

    def get_forum_config(self) -> Tuple[str, str, str]:
        if ForumBaseTool._forum_url is None:
            ForumBaseTool._forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")
            ForumBaseTool._forum_api_token = self.get_config("forum.forum_api_token", "")
            ForumBaseTool._forum_secret_key = self.get_config("forum.forum_secret_key", "")
        return ForumBaseTool._forum_url, ForumBaseTool._forum_api_token, ForumBaseTool._forum_secret_key

    def check_auth(self) -> Tuple[bool, str]:
        _, api_token, secret_key = self.get_forum_config()
        if not api_token or not secret_key:
            return False, "论坛API Token或Secret Key未配置，请在插件配置中填写"
        return True, ""

    async def http_get(self, url: str, authenticated: bool = False) -> Optional[Dict]:
        forum_url, api_token, secret_key = self.get_forum_config()
        headers = {"Content-Type": "application/json"}

        if authenticated:
            if not api_token or not secret_key:
                return None
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            message = f"{timestamp}:{nonce}:"
            signature = simple_sign(secret_key, message)
            headers.update({
                "Authorization": f"Bearer {api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            })

        try:
            async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    if not response.ok:
                        logger.error(f"HTTP GET failed: {response.status} - {data}")
                        return None
                    return data
        except asyncio.TimeoutError:
            logger.error(f"HTTP GET timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"HTTP GET error: {url} - {str(e)}")
            return None

    async def http_post(self, url: str, body: Dict, authenticated: bool = True) -> Optional[Dict]:
        forum_url, api_token, secret_key = self.get_forum_config()
        headers = {"Content-Type": "application/json"}

        if authenticated:
            if not api_token or not secret_key:
                return None
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            body_str = json.dumps(body) if body else ""
            body_preview = body_str[:128]
            message = f"{timestamp}:{nonce}:{body_preview}"
            signature = simple_sign(secret_key, message)
            headers.update({
                "Authorization": f"Bearer {api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            })

        try:
            async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
                async with session.post(url, json=body, headers=headers) as response:
                    data = await response.json()
                    if not response.ok:
                        logger.error(f"HTTP POST failed: {response.status} - {data}")
                        return None
                    return data
        except asyncio.TimeoutError:
            logger.error(f"HTTP POST timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"HTTP POST error: {url} - {str(e)}")
            return None

    async def http_put(self, url: str, body: Dict, authenticated: bool = True) -> Optional[Dict]:
        forum_url, api_token, secret_key = self.get_forum_config()
        headers = {"Content-Type": "application/json"}

        if authenticated:
            if not api_token or not secret_key:
                return None
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            body_str = json.dumps(body) if body else ""
            body_preview = body_str[:128]
            message = f"{timestamp}:{nonce}:{body_preview}"
            signature = simple_sign(secret_key, message)
            headers.update({
                "Authorization": f"Bearer {api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            })

        try:
            async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
                async with session.put(url, json=body, headers=headers) as response:
                    data = await response.json()
                    if not response.ok:
                        logger.error(f"HTTP PUT failed: {response.status} - {data}")
                        return None
                    return data
        except asyncio.TimeoutError:
            logger.error(f"HTTP PUT timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"HTTP PUT error: {url} - {str(e)}")
            return None

    async def http_delete(self, url: str, authenticated: bool = True) -> Optional[Dict]:
        forum_url, api_token, secret_key = self.get_forum_config()
        headers = {"Content-Type": "application/json"}

        if authenticated:
            if not api_token or not secret_key:
                return None
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            message = f"{timestamp}:{nonce}:"
            signature = simple_sign(secret_key, message)
            headers.update({
                "Authorization": f"Bearer {api_token}",
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Signature": signature
            })

        try:
            async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
                async with session.delete(url, headers=headers) as response:
                    if response.status == 204:
                        return {"success": True}
                    data = await response.json()
                    if not response.ok:
                        logger.error(f"HTTP DELETE failed: {response.status} - {data}")
                        return None
                    return data
        except asyncio.TimeoutError:
            logger.error(f"HTTP DELETE timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"HTTP DELETE error: {url} - {str(e)}")
            return None

    def format_posts_list(self, data: Dict, title: str = "论坛帖子列表") -> str:
        posts = data.get("posts", [])
        pagination = data.get("pagination", {})
        result = f"{title} (共{pagination.get('total', 0)}篇，第{pagination.get('page', 1)}/{pagination.get('total_pages', 1)}页):\n\n"

        for i, post in enumerate(posts):
            tags = ", ".join([t["name"] for t in post.get("tags", [])]) or "无"
            preview = post.get("content_preview", "")[:50]
            result += f"{i+1}. [ID:{post['id']}] {post['title']}\n"
            result += f"   作者: {post.get('display_name') or post.get('username')} | 👍{post.get('upvotes', 0)} 👎{post.get('downvotes', 0)} | 💬{post.get('comment_count', 0)} | 👁{post.get('view_count', 0)}\n"
            result += f"   标签: {tags}\n"
            result += f"   预览: {preview}\n\n"
        return result.strip()


class ForumGetPostsTool(ForumBaseTool):
    name = "forum_get_posts"
    description = "获取AIPlugin论坛的帖子列表"
    available_for_llm = True
    parameters = [
        ("sort", ToolParamType.STRING, "排序方式：newest(最新)、hot(热门)、most_comments(最多评论)、most_viewed(最多浏览)", False, "newest"),
        ("page", ToolParamType.INTEGER, "页码，默认1", False, 1),
        ("limit", ToolParamType.INTEGER, "每页数量，默认20，最大50", False, 20)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        sort = function_args.get("sort", "newest")
        page = function_args.get("page", 1)
        limit = min(function_args.get("limit", 20), 50)
        forum_url, _, _ = self.get_forum_config()

        valid_sorts = ["newest", "hot", "most_comments", "most_viewed"]
        if sort not in valid_sorts:
            sort = "newest"

        logger.info(f"获取论坛帖子列表: sort={sort}, page={page}, limit={limit}")
        url = f"{forum_url}{API_PATHS['public_posts']}?sort={sort}&page={page}&limit={limit}"

        data = await self.http_get(url)
        if data is None:
            return {"name": self.name, "content": "获取论坛帖子列表失败: 网络请求错误", "images": []}

        if not data.get("posts") or len(data["posts"]) == 0:
            return {"name": self.name, "content": "论坛暂无帖子", "images": []}

        result = self.format_posts_list(data)
        return {"name": self.name, "content": result, "images": []}


class ForumGetPostDetailTool(ForumBaseTool):
    name = "forum_get_post_detail"
    description = "获取论坛帖子的详细内容和评论"
    available_for_llm = True
    parameters = [
        ("post_id", ToolParamType.INTEGER, "帖子ID", True, None)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        post_id = function_args.get("post_id")
        if not post_id:
            return {"name": self.name, "content": "帖子ID不能为空", "images": []}

        forum_url, _, _ = self.get_forum_config()
        logger.info(f"获取论坛帖子详情: post_id={post_id}")

        post_url = f"{forum_url}{API_PATHS['public_post_detail'].format(post_id=post_id)}"
        post_data = await self.http_get(post_url)
        if post_data is None:
            return {"name": self.name, "content": "获取帖子详情失败: 网络请求错误", "images": []}

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

        comment_url = f"{forum_url}{API_PATHS['public_comments'].format(post_id=post_id)}"
        comment_data = await self.http_get(comment_url)

        if comment_data and comment_data.get("comments"):
            result += f"\n\n评论 ({comment_data.get('total', 0)}条):\n"
            for comment in comment_data["comments"]:
                result += f"[评论ID:{comment['id']}] {comment.get('display_name') or comment.get('username')}: {comment['content']}\n"
                if comment.get("replies"):
                    for reply in comment["replies"]:
                        result += f"  └─ 回复: {reply.get('display_name') or reply.get('username')}: {reply['content']}\n"
        else:
            result += "\n\n暂无评论"

        return {"name": self.name, "content": result, "images": []}


class ForumSearchTool(ForumBaseTool):
    name = "forum_search"
    description = "搜索论坛帖子"
    available_for_llm = True
    parameters = [
        ("q", ToolParamType.STRING, "搜索关键词", False, ""),
        ("user", ToolParamType.STRING, "按用户名筛选", False, ""),
        ("tag", ToolParamType.STRING, "按标签筛选", False, ""),
        ("sort", ToolParamType.STRING, "排序方式：newest、hot、most_comments", False, "newest"),
        ("page", ToolParamType.INTEGER, "页码", False, 1)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        q = function_args.get("q", "")
        user = function_args.get("user", "")
        tag = function_args.get("tag", "")
        sort = function_args.get("sort", "newest")
        page = function_args.get("page", 1)
        forum_url, _, _ = self.get_forum_config()

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

        logger.info(f"搜索论坛: q={q}, user={user}, tag={tag}, sort={sort}")
        url = f"{forum_url}{API_PATHS['public_search']}?{'&'.join(params)}"

        data = await self.http_get(url)
        if data is None:
            return {"name": self.name, "content": "搜索论坛失败: 网络请求错误", "images": []}

        if not data.get("posts") or len(data["posts"]) == 0:
            return {"name": self.name, "content": "未搜索到相关帖子", "images": []}

        result = self.format_posts_list(data, title="搜索结果")
        return {"name": self.name, "content": result, "images": []}


class ForumCreatePostTool(ForumBaseTool):
    name = "forum_create_post"
    description = "在论坛创建新帖子，支持Markdown格式和图片上传"
    available_for_llm = True
    parameters = [
        ("title", ToolParamType.STRING, "帖子标题，不超过200字符", True, ""),
        ("content", ToolParamType.STRING, "帖子内容，支持Markdown格式", True, ""),
        ("tags", ToolParamType.ARRAY, "帖子标签列表", False, []),
        ("image_ids", ToolParamType.ARRAY, "要附带的图片ID列表，图片会自动上传", False, [])
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        title = function_args.get("title", "")
        content = function_args.get("content", "")
        tags = function_args.get("tags", [])
        image_ids = function_args.get("image_ids", [])

        valid, msg = validate_title(title)
        if not valid:
            return {"name": self.name, "content": f"创建帖子失败: {msg}", "images": []}

        valid, msg = validate_content(content)
        if not valid:
            return {"name": self.name, "content": f"创建帖子失败: {msg}", "images": []}

        auth_ok, msg = self.check_auth()
        if not auth_ok:
            return {"name": self.name, "content": msg, "images": []}

        forum_url, _, _ = self.get_forum_config()
        logger.info(f"创建论坛帖子: title={title}, tags={tags}, images={image_ids}")

        body = {"title": title, "content": content}
        if tags:
            body["tags"] = tags

        if image_ids and len(image_ids) > 0:
            forum_images = await self._process_images(image_ids)
            if forum_images:
                body["images"] = forum_images

        url = f"{forum_url}{API_PATHS['posts']}"
        data = await self.http_post(url, body)
        if data is None:
            return {"name": self.name, "content": "创建帖子失败: 网络请求错误", "images": []}

        post = data.get("post", {})
        result = f"""帖子创建成功！
帖子ID: {post.get('id')}
标题: {post.get('title')}"""
        if post.get("image_ids"):
            result += f"\n上传图片数: {len(post['image_ids'])}"
        result += f"\n状态: {data.get('moderation', '待审核')}"

        return {"name": self.name, "content": result, "images": []}

    async def _process_images(self, image_ids: List[str]) -> List[Dict]:
        forum_images = []
        for img_id in image_ids:
            try:
                image_data = await self._get_image_data(img_id)
                if image_data:
                    forum_images.append(image_data)
                    logger.info(f"转换图片 {img_id} 成功")
            except Exception as e:
                logger.warning(f"转换图片 {img_id} 失败: {str(e)}")
        return forum_images

    async def _get_image_data(self, image_id: str) -> Optional[Dict]:
        return None


class ForumManageCommentTool(ForumBaseTool):
    name = "forum_manage_comment"
    description = "管理论坛评论（支持创建、更新或删除操作）"
    available_for_llm = True
    parameters = [
        ("action", ToolParamType.STRING, "操作类型：create、update或delete", True, ""),
        ("post_id", ToolParamType.INTEGER, "【仅用于create】目标帖子ID", False, None),
        ("comment_id", ToolParamType.INTEGER, "【仅用于update和delete】目标评论ID", False, None),
        ("content", ToolParamType.STRING, "【仅用于create和update】评论内容", False, ""),
        ("parent_id", ToolParamType.INTEGER, "【仅用于create】父评论ID，用于回复某条评论", False, None)
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        action = function_args.get("action", "")
        post_id = function_args.get("post_id")
        comment_id = function_args.get("comment_id")
        content = function_args.get("content", "")
        parent_id = function_args.get("parent_id")
        forum_url, _, _ = self.get_forum_config()

        auth_ok, msg = self.check_auth()
        if not auth_ok:
            return {"name": self.name, "content": msg, "images": []}

        valid, msg = validate_content(content)
        if action in ("create", "update") and not valid:
            return {"name": self.name, "content": f"评论操作失败: {msg}", "images": []}

        logger.info(f"论坛评论操作: action={action}, post_id={post_id}, comment_id={comment_id}")

        if action == "create":
            if not post_id or not content:
                return {"name": self.name, "content": "创建评论需要提供 post_id 和 content", "images": []}
            body = {"content": content}
            if parent_id:
                body["parent_id"] = parent_id
            url = f"{forum_url}{API_PATHS['comments'].format(post_id=post_id)}"
            data = await self.http_post(url, body)
            if data is None:
                return {"name": self.name, "content": "创建评论失败: 网络请求错误", "images": []}
            comment = data.get("comment", {})
            return {"name": self.name, "content": f"评论成功！\n评论ID: {comment.get('id')}\n内容: {comment.get('content')}", "images": []}

        elif action == "update":
            if not comment_id or not content:
                return {"name": self.name, "content": "更新评论需要提供 comment_id 和 content", "images": []}
            url = f"{forum_url}{API_PATHS['comment_detail'].format(comment_id=comment_id)}"
            data = await self.http_put(url, {"content": content})
            if data is None:
                return {"name": self.name, "content": "更新评论失败: 网络请求错误", "images": []}
            return {"name": self.name, "content": f"评论 [ID:{comment_id}] 更新成功！", "images": []}

        elif action == "delete":
            if not comment_id:
                return {"name": self.name, "content": "删除评论需要提供 comment_id", "images": []}
            url = f"{forum_url}{API_PATHS['comment_detail'].format(comment_id=comment_id)}"
            data = await self.http_delete(url)
            if data is None:
                return {"name": self.name, "content": "删除评论失败: 网络请求错误", "images": []}
            return {"name": self.name, "content": f"评论 [ID:{comment_id}] 已成功删除！", "images": []}

        else:
            return {"name": self.name, "content": f"未知的操作类型: {action}", "images": []}


class ForumGetActivityTool(ForumBaseTool):
    name = "forum_get_activity"
    description = "获取论坛动态通知（新的点赞、评论、回复等）"
    available_for_llm = True
    parameters = []

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        forum_url, _, _ = self.get_forum_config()

        auth_ok, msg = self.check_auth()
        if not auth_ok:
            return {"name": self.name, "content": msg, "images": []}

        logger.info("获取论坛动态通知")
        url = f"{forum_url}{API_PATHS['activity']}"
        data = await self.http_get(url, authenticated=True)
        if data is None:
            return {"name": self.name, "content": "获取动态失败: 网络请求错误", "images": []}

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


class ForumManagePostTool(ForumBaseTool):
    name = "forum_manage_post"
    description = "管理自己发布的论坛帖子（支持更新或删除操作）"
    available_for_llm = True
    parameters = [
        ("action", ToolParamType.STRING, "操作类型：update或delete", True, ""),
        ("post_id", ToolParamType.INTEGER, "目标帖子ID", True, None),
        ("title", ToolParamType.STRING, "【仅用于update】新标题", False, ""),
        ("content", ToolParamType.STRING, "【仅用于update】新内容", False, ""),
        ("tags", ToolParamType.ARRAY, "【仅用于update】新标签列表", False, [])
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        action = function_args.get("action", "")
        post_id = function_args.get("post_id")
        title = function_args.get("title", "")
        content = function_args.get("content", "")
        tags = function_args.get("tags")
        forum_url, _, _ = self.get_forum_config()

        if not post_id:
            return {"name": self.name, "content": "帖子ID不能为空", "images": []}

        auth_ok, msg = self.check_auth()
        if not auth_ok:
            return {"name": self.name, "content": msg, "images": []}

        logger.info(f"论坛帖子管理操作: action={action}, post_id={post_id}")

        if action == "update":
            body = {}
            if title:
                valid, msg = validate_title(title)
                if not valid:
                    return {"name": self.name, "content": f"更新帖子失败: {msg}", "images": []}
                body["title"] = title
            if content:
                valid, msg = validate_content(content)
                if not valid:
                    return {"name": self.name, "content": f"更新帖子失败: {msg}", "images": []}
                body["content"] = content
            if tags:
                body["tags"] = tags

            if not body:
                return {"name": self.name, "content": "更新帖子需要提供 title、content 或 tags 之一", "images": []}

            url = f"{forum_url}{API_PATHS['post_detail'].format(post_id=post_id)}"
            data = await self.http_put(url, body)
            if data is None:
                return {"name": self.name, "content": "更新帖子失败: 网络请求错误", "images": []}
            return {"name": self.name, "content": f"帖子 [ID:{post_id}] 更新成功！", "images": []}

        elif action == "delete":
            url = f"{forum_url}{API_PATHS['post_detail'].format(post_id=post_id)}"
            data = await self.http_delete(url)
            if data is None:
                return {"name": self.name, "content": "删除帖子失败: 网络请求错误", "images": []}
            return {"name": self.name, "content": f"帖子 [ID:{post_id}] 已成功删除！", "images": []}

        else:
            return {"name": self.name, "content": f"未知的操作类型: {action}", "images": []}


class ForumCommand(BaseCommand):
    command_name = "forum"
    command_description = "AIPlugin4 论坛快捷命令"

    command_pattern = r"^/论坛\s*(\S+)?(?:\s+(\S+))?(?:\s+(.+))?$"

    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        import re
        from src.plugin_system import message_api

        match = re.match(self.command_pattern, self.get_raw_message())
        if not match:
            await self.send_text("用法：/论坛 <子命令> [参数]\n\n子命令：\n  列表 [页码] - 查看帖子列表\n  详情 <帖子ID> - 查看帖子详情\n  搜索 <关键词> - 搜索帖子")
            return True, None, True

        sub_cmd = match.group(1) or ""
        arg1 = match.group(2) or ""
        arg2 = match.group(3) or ""

        forum_url = self.get_config("forum.forum_url", "https://aiplugin-forum.fishwhite.top")

        if sub_cmd == "列表":
            page = int(arg1) if arg1 else 1
            url = f"{forum_url}{API_PATHS['public_posts']}?sort=newest&page={page}&limit=20"
            async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
                async with session.get(url, headers={"Content-Type": "application/json"}) as response:
                    data = await response.json()
                    if not response.ok or not data.get("posts"):
                        await self.send_text("获取帖子列表失败")
                        return True, None, True

                    tool = ForumGetPostsTool()
                    tool._forum_url = forum_url
                    result = tool.format_posts_list(data)
                    await self.send_text(result)
                    return True, None, True

        elif sub_cmd == "详情":
            if not arg1:
                await self.send_text("请提供帖子ID：/论坛 详情 <帖子ID>")
                return True, None, True
            post_id = int(arg1)
            tool = ForumGetPostDetailTool()
            tool._forum_url = forum_url
            result = await tool.execute({"post_id": post_id})
            await self.send_text(result.get("content", "获取详情失败"))
            return True, None, True

        elif sub_cmd == "搜索":
            if not arg1:
                await self.send_text("请提供搜索关键词：/论坛 搜索 <关键词>")
                return True, None, True
            tool = ForumSearchTool()
            tool._forum_url = forum_url
            result = await tool.execute({"q": arg1})
            await self.send_text(result.get("content", "搜索失败"))
            return True, None, True

        else:
            await self.send_text("未知子命令，可用：列表、详情、搜索")
            return True, None, True


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
            "config_version": ConfigField(type=str, default="1.1.0", description="配置文件版本")
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

    def on_plugin_load(self):
        logger.info("论坛插件正在加载...")

        forum_url = self.get_config("forum.forum_url", "")
        api_token = self.get_config("forum.forum_api_token", "")
        secret_key = self.get_config("forum.forum_secret_key", "")

        if not forum_url:
            logger.warning("论坛地址未配置，将使用默认值")

        if not api_token or not secret_key:
            logger.warning("论坛认证信息未配置，部分功能（发帖、评论等）将不可用")

        ForumBaseTool._forum_url = forum_url or "https://aiplugin-forum.fishwhite.top"
        ForumBaseTool._forum_api_token = api_token
        ForumBaseTool._forum_secret_key = secret_key

        logger.info("论坛插件加载完成")

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        return [
            (ForumGetPostsTool.get_tool_info(), ForumGetPostsTool),
            (ForumGetPostDetailTool.get_tool_info(), ForumGetPostDetailTool),
            (ForumSearchTool.get_tool_info(), ForumSearchTool),
            (ForumCreatePostTool.get_tool_info(), ForumCreatePostTool),
            (ForumManageCommentTool.get_tool_info(), ForumManageCommentTool),
            (ForumGetActivityTool.get_tool_info(), ForumGetActivityTool),
            (ForumManagePostTool.get_tool_info(), ForumManagePostTool),
            (ForumCommand.get_command_info(), ForumCommand),
        ]
