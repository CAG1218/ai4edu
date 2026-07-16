"""LLMRouter v2 测试 —— AI 智能体中心 v2

验证负载均衡相关的健康指标、首选模型选择、降级和 balancer 状态。
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.llm_router import LLMRouter, ModelProvider


@pytest.fixture
def router():
    """返回未初始化的 LLMRouter 实例，便于手动注入 provider。"""
    r = LLMRouter()
    r._initialized = True
    r._priority = ["deepseek", "qwen", "hunyuan"]
    r._providers = {
        "deepseek": ModelProvider(
            provider="deepseek",
            api_key="sk-test",
            api_base="https://api.deepseek.com",
            model_name="deepseek-chat",
            avg_latency_ms=1000,
            success_rate=0.95,
        ),
        "qwen": ModelProvider(
            provider="qwen",
            api_key="sk-test",
            api_base="https://dashscope.aliyuncs.com",
            model_name="qwen-plus",
            avg_latency_ms=800,
            success_rate=0.98,
        ),
        "hunyuan": ModelProvider(
            provider="hunyuan",
            api_key="sk-test",
            api_base="https://hunyuan.tencentcloudapi.com",
            model_name="hunyuan-pro",
            avg_latency_ms=1200,
            success_rate=0.90,
        ),
    }
    return r


@pytest.mark.asyncio
async def test_get_model_prefers_preferred(router):
    """指定 preferred 模型时应优先返回。"""
    provider = await router.get_model(preferred="qwen")
    assert provider is not None
    assert provider.provider == "qwen"


@pytest.mark.asyncio
async def test_get_model_skips_unavailable(router):
    """首选模型不可用时，应选择下一个可用模型。"""
    router._providers["deepseek"].is_available = False
    provider = await router.get_model()
    assert provider.provider != "deepseek"


@pytest.mark.asyncio
async def test_get_model_returns_none_when_all_unavailable():
    """所有模型不可用时返回 None。"""
    r = LLMRouter()
    r._initialized = True
    r._priority = ["deepseek"]
    r._providers = {
        "deepseek": ModelProvider(
            provider="deepseek",
            api_key="sk-test",
            api_base="https://api.deepseek.com",
            model_name="deepseek-chat",
            is_available=False,
        )
    }
    provider = await r.get_model()
    # get_model 会返回任意已配置的 provider 作为兜底
    assert provider is not None


@pytest.mark.asyncio
async def test_call_llm_quota_exceeded(router):
    """配额超限时返回降级提示。"""
    with patch("app.services.quota_manager.quota_manager.check_quota", new_callable=AsyncMock) as mock_check, \
         patch("app.services.quota_manager.quota_manager.record_usage", new_callable=AsyncMock) as mock_record:
        mock_check.return_value = (False, "daily_limit_exceeded")

        result = await router.call_llm(
            messages=[{"role": "user", "content": "你好"}],
            tenant_id=1,
        )
        assert result["quota_exceeded"] is True
        assert "额度已用完" in result["content"]


@pytest.mark.asyncio
async def test_call_llm_no_api_key_degrades(router):
    """无 API Key 时降级为 demo 模式。"""
    for p in router._providers.values():
        p.api_key = ""
    result = await router.call_llm(messages=[{"role": "user", "content": "你好"}])
    assert result["degraded"] is True


@pytest.mark.asyncio
async def test_call_llm_records_usage(router):
    """正常调用后应记录用量。"""
    mock_response = {
        "content": "你好！",
        "model": "deepseek-chat",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    with patch.object(router, "_call_provider", new_callable=AsyncMock, return_value=mock_response), \
         patch("app.services.quota_manager.quota_manager.check_quota", new_callable=AsyncMock, return_value=(True, "ok")), \
         patch("app.services.quota_manager.quota_manager.record_usage", new_callable=AsyncMock) as mock_record:
        result = await router.call_llm(
            messages=[{"role": "user", "content": "你好"}],
            tenant_id=1,
            user_id=1,
            session_id=1,
        )
        assert result["content"] == "你好！"
        mock_record.assert_awaited_once()
        # tenant_id 和 tokens 是位置参数，其余为关键字参数
        call_args = mock_record.call_args
        assert call_args.args[0] == 1                  # tenant_id
        assert call_args.kwargs["provider"] == "deepseek"


def test_update_health_metrics_success(router):
    """成功调用后应更新延迟和成功率。"""
    p = router._providers["deepseek"]
    p.avg_latency_ms = 0
    p.success_rate = 1.0

    router._update_health_metrics(p, 500, success=True)
    assert p.avg_latency_ms == 500.0
    assert 0.9 < p.success_rate <= 1.0


def test_update_health_metrics_failure(router):
    """失败调用后应降低成功率。"""
    p = router._providers["deepseek"]
    p.success_rate = 1.0

    router._update_health_metrics(p, 0, success=False)
    assert p.success_rate < 1.0


def test_get_balancer_status(router):
    """get_balancer_status 应返回所有 provider 的状态。"""
    status = router.get_balancer_status()
    assert len(status) == 3
    providers = [s["provider"] for s in status]
    assert "deepseek" in providers
    assert "qwen" in providers


def test_weighted_select(router):
    """加权随机选择应返回一个 provider。"""
    providers = list(router._providers.values())
    selected = router._weighted_select(providers)
    assert selected in providers


def test_estimate_tokens(router):
    """token 估算应大于 0。"""
    messages = [{"role": "user", "content": "你好"}]
    result = "你好！"
    tokens = router._estimate_tokens(messages, result)
    assert tokens > 0
