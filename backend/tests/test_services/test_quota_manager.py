"""QuotaManager 测试 —— AI 智能体中心 v2

使用 mock Redis 和内存 AsyncSession 测试配额检查、用量记录。
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.config import settings
from app.models.usage import TenantQuota
from app.services.quota_manager import QuotaManager


@pytest.fixture
def fake_redis():
    """模拟 Redis 客户端。"""
    store = {}

    class FakeRedis:
        async def get(self, key):
            return store.get(key, 0)

        async def set(self, key, value, ex=None):
            store[key] = value

        async def incrby(self, key, value):
            store[key] = store.get(key, 0) + value
            return store[key]

        async def expire(self, key, ttl):
            pass

    return FakeRedis(), store


@pytest.fixture
def quota_manager(fake_redis):
    qm = QuotaManager()
    qm._redis = fake_redis[0]
    return qm


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_check_quota_with_default_config(quota_manager, mock_db):
    """无配额配置时，应使用默认配置并返回允许。"""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    allowed, reason = await quota_manager.check_quota(1, db=mock_db)
    assert allowed is True
    assert reason == "ok"


@pytest.mark.asyncio
async def test_check_quota_daily_exceeded(quota_manager, mock_db, fake_redis):
    """日 token 超限应拒绝。"""
    _, store = fake_redis
    today = date.today().isoformat()
    store[f"{settings.QUOTA_REDIS_KEY_PREFIX}:1:daily:{today}"] = 500000

    quota = TenantQuota(
        tenant_id=1,
        daily_token_limit=500000,
        monthly_token_limit=10000000,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = quota
    mock_db.execute.return_value = mock_result

    allowed, reason = await quota_manager.check_quota(1, estimated_tokens=100, db=mock_db)
    assert allowed is False
    assert "exceeded" in reason.lower()


@pytest.mark.asyncio
async def test_check_quota_monthly_exceeded(quota_manager, mock_db, fake_redis):
    """月 token 超限应拒绝。"""
    _, store = fake_redis
    year_month = date.today().strftime("%Y-%m")
    store[f"{settings.QUOTA_REDIS_KEY_PREFIX}:1:monthly:{year_month}"] = 10000000

    quota = TenantQuota(
        tenant_id=1,
        daily_token_limit=500000,
        monthly_token_limit=10000000,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = quota
    mock_db.execute.return_value = mock_result

    allowed, reason = await quota_manager.check_quota(1, estimated_tokens=100, db=mock_db)
    assert allowed is False


@pytest.mark.asyncio
async def test_record_usage_updates_redis(quota_manager, fake_redis):
    """记录用量应增加 Redis 日/月计数和请求次数。"""
    _, store = fake_redis

    await quota_manager.record_usage(
        tenant_id=1,
        tokens=1500,
        provider="deepseek",
        model_name="deepseek-chat",
    )

    today = date.today().isoformat()
    year_month = date.today().strftime("%Y-%m")
    assert store[f"{settings.QUOTA_REDIS_KEY_PREFIX}:1:daily:{today}"] == 1500
    assert store[f"{settings.QUOTA_REDIS_KEY_PREFIX}:1:monthly:{year_month}"] == 1500


@pytest.mark.asyncio
async def test_get_usage_returns_correct_values(quota_manager, fake_redis, mock_db):
    """get_usage 应返回当前 Redis 中的日/月累计值。"""
    _, store = fake_redis
    today = date.today().isoformat()
    year_month = date.today().strftime("%Y-%m")
    store[f"{settings.QUOTA_REDIS_KEY_PREFIX}:1:daily:{today}"] = 12345
    store[f"{settings.QUOTA_REDIS_KEY_PREFIX}:1:monthly:{year_month}"] = 67890

    quota = TenantQuota(
        tenant_id=1,
        daily_token_limit=100000,
        monthly_token_limit=1000000,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = quota
    mock_db.execute.return_value = mock_result

    usage = await quota_manager.get_usage(1, db=mock_db)
    assert usage["daily_used"] == 12345
    assert usage["monthly_used"] == 67890
    assert usage["daily_limit"] == 100000


@pytest.mark.asyncio
async def test_get_usage_without_tenant_returns_defaults(quota_manager):
    """无 tenant_id 时返回默认值。"""
    usage = await quota_manager.get_usage(0)
    assert usage["daily_used"] == 0
    assert usage["daily_limit"] == settings.QUOTA_DEFAULT_DAILY_TOKENS


@pytest.mark.asyncio
async def test_get_tenant_strategy(quota_manager, mock_db):
    """应返回 DB 中配置的策略。"""
    quota = TenantQuota(tenant_id=1, strategy="sticky")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = quota
    mock_db.execute.return_value = mock_result

    strategy = await quota_manager.get_tenant_strategy(1, mock_db)
    assert strategy == "sticky"
