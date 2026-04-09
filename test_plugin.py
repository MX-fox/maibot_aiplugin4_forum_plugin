import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, '.')

from plugin import (
    simple_sign,
    generate_nonce,
    validate_title,
    validate_content,
    ForumBaseTool,
    ForumGetPostsTool,
    ForumCreatePostTool,
    ForumManageCommentTool,
)


class TestSimpleSign:
    def test_simple_sign_consistency(self):
        secret = "test_secret"
        message = "test_message"
        sig1 = simple_sign(secret, message)
        sig2 = simple_sign(secret, message)
        assert sig1 == sig2

    def test_simple_sign_different_secrets(self):
        message = "test_message"
        sig1 = simple_sign("secret1", message)
        sig2 = simple_sign("secret2", message)
        assert sig1 != sig2

    def test_simple_sign_different_messages(self):
        secret = "test_secret"
        sig1 = simple_sign(secret, "message1")
        sig2 = simple_sign(secret, "message2")
        assert sig1 != sig2

    def test_simple_sign_format(self):
        sig = simple_sign("secret", "message")
        assert len(sig) == 8
        assert all(c in '0123456789abcdef' for c in sig)


class TestGenerateNonce:
    def test_nonce_length(self):
        nonce = generate_nonce()
        assert len(nonce) >= 8

    def test_nonce_uniqueness(self):
        nonces = [generate_nonce() for _ in range(100)]
        assert len(set(nonces)) == 100


class TestValidation:
    def test_validate_title_empty(self):
        valid, msg = validate_title("")
        assert valid == False
        assert "空" in msg

    def test_validate_title_too_long(self):
        valid, msg = validate_title("a" * 201)
        assert valid == False
        assert "200" in msg

    def test_validate_title_valid(self):
        valid, msg = validate_title("正常标题")
        assert valid == True
        assert msg == ""

    def test_validate_content_empty(self):
        valid, msg = validate_content("")
        assert valid == False
        assert "空" in msg

    def test_validate_content_too_long(self):
        valid, msg = validate_content("a" * 50001)
        assert valid == False
        assert "50000" in msg

    def test_validate_content_valid(self):
        valid, msg = validate_content("正常内容")
        assert valid == True


class TestForumBaseTool:
    def test_check_auth_no_credentials(self):
        tool = ForumBaseTool()
        tool._forum_api_token = ""
        tool._forum_secret_key = ""
        valid, msg = tool.check_auth()
        assert valid == False

    def test_check_auth_with_credentials(self):
        tool = ForumBaseTool()
        tool._forum_api_token = "token"
        tool._forum_secret_key = "secret"
        valid, msg = tool.check_auth()
        assert valid == True


class TestForumGetPostsTool:
    @pytest.mark.asyncio
    async def test_execute_invalid_sort(self):
        tool = ForumGetPostsTool()
        tool._forum_url = "https://example.com"
        tool._forum_api_token = ""
        tool._forum_secret_key = ""

        with patch.object(tool, 'http_get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "posts": [{"id": 1, "title": "Test"}],
                "pagination": {"total": 1, "page": 1, "total_pages": 1}
            }
            result = await tool.execute({"sort": "invalid_sort"})
            assert "forum_get_posts" in result["name"]
            mock_get.assert_called_once()


class TestForumCreatePostTool:
    @pytest.mark.asyncio
    async def test_execute_no_auth(self):
        tool = ForumCreatePostTool()
        tool._forum_url = "https://example.com"
        tool._forum_api_token = ""
        tool._forum_secret_key = ""

        result = await tool.execute({
            "title": "Test",
            "content": "Content"
        })
        assert "未配置" in result["content"]

    @pytest.mark.asyncio
    async def test_execute_empty_title(self):
        tool = ForumCreatePostTool()
        tool._forum_url = "https://example.com"
        tool._forum_api_token = "token"
        tool._forum_secret_key = "secret"

        result = await tool.execute({
            "title": "",
            "content": "Content"
        })
        assert "失败" in result["content"]

    @pytest.mark.asyncio
    async def test_execute_title_too_long(self):
        tool = ForumCreatePostTool()
        tool._forum_url = "https://example.com"
        tool._forum_api_token = "token"
        tool._forum_secret_key = "secret"

        result = await tool.execute({
            "title": "a" * 201,
            "content": "Content"
        })
        assert "失败" in result["content"]


class TestForumManageCommentTool:
    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        tool = ForumManageCommentTool()
        tool._forum_url = "https://example.com"
        tool._forum_api_token = "token"
        tool._forum_secret_key = "secret"

        result = await tool.execute({"action": "unknown"})
        assert "未知" in result["content"]

    @pytest.mark.asyncio
    async def test_execute_create_without_post_id(self):
        tool = ForumManageCommentTool()
        tool._forum_url = "https://example.com"
        tool._forum_api_token = "token"
        tool._forum_secret_key = "secret"

        result = await tool.execute({
            "action": "create",
            "content": "Test comment"
        })
        assert "post_id" in result["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
