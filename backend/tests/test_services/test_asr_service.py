"""
ASR 多 Provider 抽象层测试
测试范围：工厂方法选择、Mock provider 返回、Aliyun/Tencent 配置判断、兜底逻辑
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.asr_service import (
    AliyunASRProvider,
    ASRProviderFactory,
    ASRResult,
    MockASRProvider,
    TencentASRProvider,
)


# ============================================================================
# ASRResult 数据类测试
# ============================================================================

class TestASRResult:
    """ASRResult 数据类测试"""

    def test_default_values(self):
        """默认值正确"""
        result = ASRResult()
        assert result.transcript == ""
        assert result.segments == []
        assert result.provider == "unknown"
        assert result.duration_seconds == 0.0

    def test_custom_values(self):
        """自定义值正确"""
        segments = [{"start": 0.0, "end": 5.0, "text": "hello"}]
        result = ASRResult(
            transcript="hello",
            segments=segments,
            provider="aliyun",
            duration_seconds=5.0,
        )
        assert result.transcript == "hello"
        assert result.segments == segments
        assert result.provider == "aliyun"
        assert result.duration_seconds == 5.0


# ============================================================================
# MockASRProvider 测试
# ============================================================================

class TestMockASRProvider:
    """MockASRProvider 测试"""

    def test_provider_name(self):
        """provider_name 返回 'mock'"""
        provider = MockASRProvider()
        assert provider.provider_name == "mock"

    async def test_transcribe_returns_result(self):
        """transcribe 返回 ASRResult 且 provider 为 mock"""
        provider = MockASRProvider()
        result = await provider.transcribe("http://example.com/audio.wav")

        assert isinstance(result, ASRResult)
        assert result.provider == "mock"
        assert result.duration_seconds == 30.0
        assert len(result.transcript) > 0
        assert len(result.segments) == 5

    async def test_transcribe_segments_have_timestamps(self):
        """segments 包含 start/end/text 字段"""
        provider = MockASRProvider()
        result = await provider.transcribe("any_url")

        for seg in result.segments:
            assert "start" in seg
            assert "end" in seg
            assert "text" in seg
            assert seg["end"] > seg["start"]

    async def test_transcript_contains_educational_content(self):
        """转录文本应包含教学内容"""
        provider = MockASRProvider()
        result = await provider.transcribe("any_url")
        assert "函数" in result.transcript or "极限" in result.transcript


# ============================================================================
# AliyunASRProvider 测试
# ============================================================================

class TestAliyunASRProvider:
    """AliyunASRProvider 测试"""

    def test_provider_name(self):
        """provider_name 返回 'aliyun'"""
        provider = AliyunASRProvider()
        assert provider.provider_name == "aliyun"

    async def test_transcribe_success(self):
        """成功转录并解析阿里云 ASR 响应"""
        provider = AliyunASRProvider()

        # Mock 提交任务响应
        submit_response = MagicMock()
        submit_response.raise_for_status = MagicMock()
        submit_response.json.return_value = {"TaskId": "task-123"}

        # Mock 轮询结果响应（成功）
        query_response = MagicMock()
        query_response.raise_for_status = MagicMock()
        query_response.json.return_value = {
            "StatusCode": 21050000,
            "Result": {
                "Sentences": [
                    {"BeginTime": 0, "EndTime": 5000, "Text": "你好"},
                    {"BeginTime": 5000, "EndTime": 10000, "Text": "世界"},
                ]
            },
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=submit_response)
        mock_client.get = AsyncMock(return_value=query_response)

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            result = await provider.transcribe("http://example.com/audio.wav")

        assert result.provider == "aliyun"
        assert result.transcript == "你好世界"
        assert len(result.segments) == 2
        assert result.segments[0]["start"] == 0.0
        assert result.segments[0]["end"] == 5.0
        assert result.duration_seconds == 10.0

    async def test_transcribe_no_task_id_raises(self):
        """提交任务未返回 TaskId 时抛出异常"""
        provider = AliyunASRProvider()

        submit_response = MagicMock()
        submit_response.raise_for_status = MagicMock()
        submit_response.json.return_value = {}  # 无 TaskId

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=submit_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await provider.transcribe("http://example.com/audio.wav")


# ============================================================================
# TencentASRProvider 测试
# ============================================================================

class TestTencentASRProvider:
    """TencentASRProvider 测试"""

    def test_provider_name(self):
        """provider_name 返回 'tencent'"""
        provider = TencentASRProvider()
        assert provider.provider_name == "tencent"

    async def test_transcribe_success(self):
        """成功转录并解析腾讯云 ASR 响应"""
        provider = TencentASRProvider()

        # Mock 提交任务响应
        submit_response = MagicMock()
        submit_response.raise_for_status = MagicMock()
        submit_response.json.return_value = {"Data": {"TaskId": 12345}}

        # Mock 轮询结果响应（成功）
        query_response = MagicMock()
        query_response.raise_for_status = MagicMock()
        query_response.json.return_value = {
            "Data": {
                "StatusStr": "success",
                "ResultText": "这是转录文本",
            }
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        # 第一次调用是提交，后续是轮询
        mock_client.post = AsyncMock(
            side_effect=[submit_response, query_response]
        )

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            result = await provider.transcribe("http://example.com/audio.wav")

        assert result.provider == "tencent"
        assert result.transcript == "这是转录文本"

    async def test_transcribe_no_task_id_raises(self):
        """提交任务未返回 TaskId 时抛出异常"""
        provider = TencentASRProvider()

        submit_response = MagicMock()
        submit_response.raise_for_status = MagicMock()
        submit_response.json.return_value = {"Data": {}}  # 无 TaskId

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=submit_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await provider.transcribe("http://example.com/audio.wav")


# ============================================================================
# ASRProviderFactory 测试
# ============================================================================

class TestASRProviderFactory:
    """ASRProviderFactory 工厂方法测试"""

    def test_factory_returns_mock_when_no_config(self):
        """无任何 API Key 配置时返回 MockASRProvider"""
        with patch("app.services.asr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent,mock"
            mock_settings.ALIYUN_ASR_APP_KEY = ""
            mock_settings.TENCENT_ASR_SECRET_ID = ""
            mock_settings.TENCENT_ASR_SECRET_KEY = ""

            provider = ASRProviderFactory.get_provider()
            assert isinstance(provider, MockASRProvider)

    def test_factory_returns_aliyun_when_configured(self):
        """配置了阿里云 ASR Key 时返回 AliyunASRProvider"""
        with patch("app.services.asr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent,mock"
            mock_settings.ALIYUN_ASR_APP_KEY = "sk-aliyun-asr-key"
            mock_settings.TENCENT_ASR_SECRET_ID = ""
            mock_settings.TENCENT_ASR_SECRET_KEY = ""

            provider = ASRProviderFactory.get_provider()
            assert isinstance(provider, AliyunASRProvider)

    def test_factory_returns_tencent_when_aliyun_unconfigured(self):
        """阿里云未配置但腾讯云已配置时返回 TencentASRProvider"""
        with patch("app.services.asr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent,mock"
            mock_settings.ALIYUN_ASR_APP_KEY = ""
            mock_settings.TENCENT_ASR_SECRET_ID = "tencent-asr-id"
            mock_settings.TENCENT_ASR_SECRET_KEY = "tencent-asr-key"

            provider = ASRProviderFactory.get_provider()
            assert isinstance(provider, TencentASRProvider)

    def test_factory_falls_back_to_mock(self):
        """所有 provider 不可用时兜底返回 MockASRProvider"""
        with patch("app.services.asr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent"
            mock_settings.ALIYUN_ASR_APP_KEY = ""
            mock_settings.TENCENT_ASR_SECRET_ID = ""
            mock_settings.TENCENT_ASR_SECRET_KEY = ""

            provider = ASRProviderFactory.get_provider()
            assert isinstance(provider, MockASRProvider)

    def test_factory_custom_priority(self):
        """自定义优先级链"""
        with patch("app.services.asr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "tencent,aliyun,mock"
            mock_settings.ALIYUN_ASR_APP_KEY = ""
            mock_settings.TENCENT_ASR_SECRET_ID = ""
            mock_settings.TENCENT_ASR_SECRET_KEY = ""

            provider = ASRProviderFactory.get_provider()
            assert isinstance(provider, MockASRProvider)

    def test_factory_empty_priority_uses_default(self):
        """空优先级字符串时使用默认值"""
        with patch("app.services.asr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = ""
            mock_settings.ALIYUN_ASR_APP_KEY = ""
            mock_settings.TENCENT_ASR_SECRET_ID = ""
            mock_settings.TENCENT_ASR_SECRET_KEY = ""

            provider = ASRProviderFactory.get_provider()
            assert isinstance(provider, MockASRProvider)

    def test_create_provider_tencent_partial_config_returns_none(self):
        """腾讯云只有 SecretID 没有 SecretKey 时返回 None"""
        with patch("app.services.asr_service.settings") as mock_settings:
            mock_settings.TENCENT_ASR_SECRET_ID = "id-only"
            mock_settings.TENCENT_ASR_SECRET_KEY = ""
            result = ASRProviderFactory._create_provider("tencent")
            assert result is None

    def test_create_provider_unknown_name_returns_none(self):
        """未知 provider 名称返回 None"""
        result = ASRProviderFactory._create_provider("unknown")
        assert result is None
