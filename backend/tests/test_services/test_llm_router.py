"""
LLMRouter 多模型路由器测试
测试范围：配置解析、模型选择、fallback 逻辑、健康检查、demo 降级模式
"""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.agents.llm_router import LLMRouter, ModelProvider
from app.agents.scene_config import SCENE_PRESETS


# ============================================================================
# ModelProvider 数据类测试
# ============================================================================

class TestModelProvider:
    """ModelProvider 数据类测试"""

    def test_is_configured_with_valid_key(self):
        """有效 API Key 时 is_configured 返回 True"""
        provider = ModelProvider(
            provider="deepseek",
            api_key="sk-real-key-12345",
            api_base="https://api.deepseek.com/v1",
            model_name="deepseek-chat",
        )
        assert provider.is_configured is True

    def test_is_configured_with_empty_key(self):
        """空 API Key 时 is_configured 返回 False"""
        provider = ModelProvider(
            provider="deepseek",
            api_key="",
            api_base="https://api.deepseek.com/v1",
            model_name="deepseek-chat",
        )
        assert provider.is_configured is False

    @pytest.mark.parametrize("invalid_key", ["sk-xxx", "xxx", "sk-your-openai-api-key"])
    def test_is_configured_with_placeholder_keys(self, invalid_key):
        """占位符 API Key 时 is_configured 返回 False"""
        provider = ModelProvider(
            provider="deepseek",
            api_key=invalid_key,
            api_base="https://api.deepseek.com/v1",
            model_name="deepseek-chat",
        )
        assert provider.is_configured is False

    def test_default_values(self):
        """默认值正确"""
        provider = ModelProvider(
            provider="qwen",
            api_key="sk-test",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name="qwen-plus",
        )
        assert provider.is_available is True
        assert provider.failure_count == 0
        assert provider.last_error_time is None
        assert provider.last_error_msg == ""
        assert provider.request_count == 0
        assert provider.window_start > 0


# ============================================================================
# LLMRouter 初始化与配置解析测试
# ============================================================================

class TestLLMRouterInit:
    """LLMRouter 初始化测试"""

    @pytest.mark.asyncio
    async def test_initialize_loads_three_providers(self):
        """初始化后应加载 deepseek/qwen/hunyuan 三个 Provider"""
        router = LLMRouter()
        await router._initialize()

        assert "deepseek" in router._providers
        assert "qwen" in router._providers
        assert "hunyuan" in router._providers
        assert len(router._providers) == 3

    @pytest.mark.asyncio
    async def test_initialize_parses_priority(self):
        """初始化后应正确解析优先级列表"""
        router = LLMRouter()
        await router._initialize()

        # 默认优先级: deepseek, qwen, hunyuan
        assert router._priority == ["deepseek", "qwen", "hunyuan"]

    @pytest.mark.asyncio
    async def test_initialize_is_idempotent(self):
        """多次调用 _initialize 应幂等"""
        router = LLMRouter()
        await router._initialize()
        providers_first = dict(router._providers)
        priority_first = list(router._priority)

        await router._initialize()
        assert router._providers == providers_first
        assert router._priority == priority_first

    @pytest.mark.asyncio
    async def test_initialize_with_custom_priority(self):
        """自定义优先级配置应正确解析"""
        router = LLMRouter()
        with patch("app.agents.llm_router.settings") as mock_settings:
            mock_settings.DEEPSEEK_API_KEY = "sk-ds"
            mock_settings.DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
            mock_settings.DEEPSEEK_MODEL = "deepseek-chat"
            mock_settings.QWEN_API_KEY = "sk-qw"
            mock_settings.QWEN_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            mock_settings.QWEN_MODEL = "qwen-plus"
            mock_settings.HUNYUAN_API_KEY = "sk-hy"
            mock_settings.HUNYUAN_API_BASE = "https://api.hunyuan.cloud.tencent.com/v1"
            mock_settings.HUNYUAN_MODEL = "hunyuan-pro"
            mock_settings.LLM_MODEL_PRIORITY = "qwen,deepseek,hunyuan"
            mock_settings.LLM_MAX_FAILURES = 2
            mock_settings.LLM_RATE_LIMIT_PER_MINUTE = 60
            mock_settings.LLM_MULTI_MODEL_ENABLED = True
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.OPENAI_API_BASE = ""
            mock_settings.OPENAI_MODEL = ""

            router._initialized = False
            await router._initialize()
            assert router._priority[0] == "qwen"


# ============================================================================
# 模型选择 get_model 测试
# ============================================================================

class TestGetModel:
    """get_model 模型选择测试"""

    @pytest.mark.asyncio
    async def test_get_model_returns_first_available(self):
        """无参数时返回优先级链中第一个可用模型"""
        router = LLMRouter()
        await router._initialize()

        # 设置 deepseek 为已配置状态
        router._providers["deepseek"].api_key = "sk-real-key"
        router._providers["qwen"].api_key = ""
        router._providers["hunyuan"].api_key = ""

        model = await router.get_model()
        assert model is not None
        assert model.provider == "deepseek"

    @pytest.mark.asyncio
    async def test_get_model_with_preferred(self):
        """preferred 参数应优先返回指定 Provider"""
        router = LLMRouter()
        await router._initialize()

        # 全部配置
        for p in router._providers.values():
            p.api_key = "sk-real-key"

        model = await router.get_model(preferred="qwen")
        assert model is not None
        assert model.provider == "qwen"

    @pytest.mark.asyncio
    async def test_get_model_with_scene_type(self):
        """scene_type 应根据场景偏好选择模型"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = "sk-real-key"

        # preview 场景偏好 qwen
        model = await router.get_model(scene_type="preview")
        assert model is not None
        assert model.provider == "qwen"

        # self_study 场景偏好 deepseek
        model = await router.get_model(scene_type="self_study")
        assert model is not None
        assert model.provider == "deepseek"

    @pytest.mark.asyncio
    async def test_get_model_preferred_over_scene(self):
        """preferred 优先级高于 scene_type"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = "sk-real-key"

        # self_study 偏好 deepseek，但指定 preferred=hunyuan
        model = await router.get_model(scene_type="self_study", preferred="hunyuan")
        assert model is not None
        assert model.provider == "hunyuan"

    @pytest.mark.asyncio
    async def test_get_model_skips_unconfigured(self):
        """应跳过未配置的 Provider"""
        router = LLMRouter()
        await router._initialize()

        router._providers["deepseek"].api_key = ""
        router._providers["qwen"].api_key = "sk-real"
        router._providers["hunyuan"].api_key = ""

        model = await router.get_model()
        assert model is not None
        assert model.provider == "qwen"

    @pytest.mark.asyncio
    async def test_get_model_skips_unavailable(self):
        """应跳过标记为不可用的 Provider"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = "sk-real-key"

        # 标记 deepseek 不可用
        router._providers["deepseek"].is_available = False

        model = await router.get_model()
        assert model is not None
        # 应 fallback 到 qwen
        assert model.provider == "qwen"

    @pytest.mark.asyncio
    async def test_get_model_all_unconfigured_returns_none(self):
        """所有 Provider 未配置时返回 None"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = ""
            p.is_available = True

        model = await router.get_model()
        assert model is None

    @pytest.mark.asyncio
    async def test_get_model_invalid_scene_type(self):
        """无效 scene_type 应回退到优先级链"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = "sk-real-key"

        model = await router.get_model(scene_type="invalid_scene")
        assert model is not None
        assert model.provider == "deepseek"


# ============================================================================
# call_llm fallback 逻辑测试
# ============================================================================

class TestCallLLMFallback:
    """call_llm fallback 容灾测试"""

    @pytest.mark.asyncio
    async def test_call_llm_no_configured_returns_demo(self):
        """无任何已配置 Provider 时降级为 demo 模式"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = ""

        result = await router.call_llm(
            messages=[{"role": "user", "content": "hello"}]
        )

        assert result["degraded"] is True
        assert result["model"] == "demo-rule-engine"
        assert result["content"] == ""
        assert result["fallback_info"] is None

    @pytest.mark.asyncio
    async def test_call_llm_success_on_first_provider(self):
        """首选 Provider 调用成功"""
        router = LLMRouter()
        await router._initialize()

        router._providers["deepseek"].api_key = "sk-real"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from DeepSeek"}}],
            "model": "deepseek-chat",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await router.call_llm(
                messages=[{"role": "user", "content": "hello"}]
            )

        assert result["degraded"] is False
        assert result["content"] == "Hello from DeepSeek"
        assert result["model"] == "deepseek-chat"
        assert result["usage"]["total_tokens"] == 15
        assert result["fallback_info"] is None

    @pytest.mark.asyncio
    async def test_call_llm_fallback_to_second_provider(self):
        """首选 Provider 失败后 fallback 到第二个"""
        router = LLMRouter()
        await router._initialize()

        router._providers["deepseek"].api_key = "sk-real-ds"
        router._providers["qwen"].api_key = "sk-real-qw"

        # 第一次调用（deepseek）抛异常，第二次（qwen）成功
        call_count = [0]

        async def mock_post(url, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:  # deepseek 失败 2 次（LLM_MAX_FAILURES=2）
                raise httpx.HTTPError("Connection refused")
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": "Hello from Qwen"}}],
                "model": "qwen-plus",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }
            return mock_resp

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = mock_post
            mock_client_cls.return_value = mock_client

            result = await router.call_llm(
                messages=[{"role": "user", "content": "hello"}]
            )

        assert result["degraded"] is False
        assert result["content"] == "Hello from Qwen"
        assert result["model"] == "qwen-plus"
        assert result["fallback_info"] is not None
        assert result["fallback_info"]["from"] == "deepseek"
        assert result["fallback_info"]["to"] == "qwen"

    @pytest.mark.asyncio
    async def test_call_llm_all_providers_fail_returns_demo(self):
        """所有 Provider 都失败时降级为 demo 模式"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = "sk-real"
            p.is_available = True
            p.failure_count = 0

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection refused"))
            mock_client_cls.return_value = mock_client

            result = await router.call_llm(
                messages=[{"role": "user", "content": "hello"}]
            )

        assert result["degraded"] is True
        assert result["model"] == "demo-rule-engine"


# ============================================================================
# 健康检查测试
# ============================================================================

class TestHealthCheck:
    """health_check 健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check_returns_all_providers(self):
        """健康检查返回所有 Provider 状态"""
        router = LLMRouter()
        await router._initialize()

        router._providers["deepseek"].api_key = "sk-real"
        router._providers["qwen"].api_key = ""
        router._providers["hunyuan"].api_key = "sk-real-hy"
        router._providers["hunyuan"].is_available = False

        results = await router.health_check()

        assert len(results) == 3

        # deepseek: available + configured
        ds = next(r for r in results if r["provider"] == "deepseek")
        assert ds["status"] == "available"
        assert ds["is_configured"] is True
        assert ds["is_default"] is True  # 第一个

        # qwen: not_configured
        qw = next(r for r in results if r["provider"] == "qwen")
        assert qw["status"] == "not_configured"
        assert qw["is_configured"] is False
        assert qw["is_default"] is False

        # hunyuan: unavailable
        hy = next(r for r in results if r["provider"] == "hunyuan")
        assert hy["status"] == "unavailable"
        assert hy["is_configured"] is True
        assert hy["is_default"] is False

    @pytest.mark.asyncio
    async def test_health_check_is_default_flag(self):
        """只有优先级链中第一个标记 is_default"""
        router = LLMRouter()
        await router._initialize()

        for p in router._providers.values():
            p.api_key = "sk-real"

        results = await router.health_check()

        defaults = [r for r in results if r["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["provider"] == "deepseek"


# ============================================================================
# has_any_configured 测试
# ============================================================================

class TestHasAnyConfigured:
    """has_any_configured 同步检查测试"""

    def test_has_any_configured_false_when_empty(self):
        """无任何 API Key 时返回 False"""
        router = LLMRouter()
        router._initialized = False

        with patch("app.agents.llm_router.settings") as mock_settings:
            mock_settings.DEEPSEEK_API_KEY = ""
            mock_settings.QWEN_API_KEY = ""
            mock_settings.HUNYUAN_API_KEY = ""
            mock_settings.OPENAI_API_KEY = ""

            assert router.has_any_configured() is False

    def test_has_any_configured_true_with_deepseek(self):
        """有 DeepSeek Key 时返回 True"""
        router = LLMRouter()
        router._initialized = False

        with patch("app.agents.llm_router.settings") as mock_settings:
            mock_settings.DEEPSEEK_API_KEY = "sk-real"
            mock_settings.QWEN_API_KEY = ""
            mock_settings.HUNYUAN_API_KEY = ""
            mock_settings.OPENAI_API_KEY = ""

            assert router.has_any_configured() is True

    def test_has_any_configured_after_init(self):
        """初始化后基于 Provider 状态检查"""
        router = LLMRouter()
        router._initialized = True
        router._providers = {
            "deepseek": ModelProvider("deepseek", "", "base", "model"),
            "qwen": ModelProvider("qwen", "sk-real", "base", "model"),
            "hunyuan": ModelProvider("hunyuan", "", "base", "model"),
        }

        assert router.has_any_configured() is True


# ============================================================================
# 错误分类与故障记录测试
# ============================================================================

class TestErrorClassification:
    """_classify_error 错误分类测试"""

    def setup_method(self):
        self.router = LLMRouter()

    @pytest.mark.parametrize("error_msg,expected", [
        ("HTTP 429 Too Many Requests", "rate_limit"),
        ("Rate limit exceeded", "rate_limit"),
        ("Request timed out after 30s", "timeout"),
        ("Connection timeout", "timeout"),
        ("HTTP 401 Unauthorized", "auth_error"),
        ("HTTP 403 Forbidden", "auth_error"),
        ("Authentication failed", "auth_error"),
        ("HTTP 500 Internal Server Error", "server_error"),
        ("HTTP 502 Bad Gateway", "server_error"),
        ("HTTP 503 Service Unavailable", "server_error"),
        ("Connection refused", "network_error"),
        ("Network unreachable", "network_error"),
        ("Some unknown error", "unknown"),
    ])
    def test_classify_error(self, error_msg, expected):
        """各类错误消息应正确分类"""
        assert self.router._classify_error(error_msg) == expected


class TestFailureRecording:
    """_record_failure / _record_success 故障记录测试"""

    def setup_method(self):
        self.router = LLMRouter()

    def test_record_failure_increments_count(self):
        """_record_failure 应递增 failure_count"""
        provider = ModelProvider("deepseek", "sk-real", "base", "model")
        self.router._record_failure(provider, "timeout error")

        assert provider.failure_count == 1
        assert provider.last_error_time is not None
        assert "timeout error" in provider.last_error_msg

    def test_record_failure_marks_unavailable_after_threshold(self):
        """超过 LLM_MAX_FAILURES 阈值后标记为不可用"""
        provider = ModelProvider("deepseek", "sk-real", "base", "model")

        with patch("app.agents.llm_router.settings") as mock_settings:
            mock_settings.LLM_MAX_FAILURES = 2

            self.router._record_failure(provider, "error1")
            assert provider.is_available is True  # 1 < 2

            self.router._record_failure(provider, "error2")
            assert provider.is_available is False  # 2 >= 2

    def test_record_success_resets_state(self):
        """_record_success 应重置 failure_count 和 is_available"""
        provider = ModelProvider("deepseek", "sk-real", "base", "model")
        provider.failure_count = 3
        provider.is_available = False
        provider.last_error_msg = "previous error"

        self.router._record_success(provider)

        assert provider.failure_count == 0
        assert provider.is_available is True
        assert provider.last_error_msg == ""


# ============================================================================
# _should_skip 速率限制测试
# ============================================================================

class TestShouldSkip:
    """_should_skip 跳过逻辑测试"""

    def setup_method(self):
        self.router = LLMRouter()

    def test_skip_unconfigured(self):
        """未配置 Provider 应跳过"""
        provider = ModelProvider("deepseek", "", "base", "model")
        assert self.router._should_skip(provider) is True

    def test_skip_unavailable(self):
        """不可用 Provider 应跳过"""
        provider = ModelProvider("deepseek", "sk-real", "base", "model")
        provider.is_available = False
        assert self.router._should_skip(provider) is True

    def test_skip_rate_limited(self):
        """触发速率限制应跳过"""
        provider = ModelProvider("deepseek", "sk-real", "base", "model")
        provider.request_count = 100

        with patch("app.agents.llm_router.settings") as mock_settings:
            mock_settings.LLM_RATE_LIMIT_PER_MINUTE = 60
            assert self.router._should_skip(provider) is True

    def test_no_skip_when_normal(self):
        """正常状态不跳过"""
        provider = ModelProvider("deepseek", "sk-real", "base", "model")
        provider.request_count = 0

        with patch("app.agents.llm_router.settings") as mock_settings:
            mock_settings.LLM_RATE_LIMIT_PER_MINUTE = 60
            assert self.router._should_skip(provider) is False

    def test_no_rate_limit_when_disabled(self):
        """速率限制为 0 时不限流"""
        provider = ModelProvider("deepseek", "sk-real", "base", "model")
        provider.request_count = 999

        with patch("app.agents.llm_router.settings") as mock_settings:
            mock_settings.LLM_RATE_LIMIT_PER_MINUTE = 0
            assert self.router._should_skip(provider) is False
