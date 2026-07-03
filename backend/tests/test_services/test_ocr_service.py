"""
OCR 多 Provider 抽象层测试
测试范围：工厂方法选择、Mock provider 返回、Aliyun/Tencent 配置判断、兜底逻辑
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ocr_service import (
    AliyunOCRProvider,
    MockOCRProvider,
    OCRProviderFactory,
    OCRResult,
    TencentOCRProvider,
)


# ============================================================================
# OCRResult 数据类测试
# ============================================================================

class TestOCRResult:
    """OCRResult 数据类测试"""

    def test_default_values(self):
        """默认值正确"""
        result = OCRResult()
        assert result.text == ""
        assert result.confidence == 0.0
        assert result.provider == "unknown"
        assert result.raw_response is None

    def test_custom_values(self):
        """自定义值正确"""
        result = OCRResult(
            text="hello",
            confidence=0.95,
            provider="aliyun",
            raw_response={"key": "val"},
        )
        assert result.text == "hello"
        assert result.confidence == 0.95
        assert result.provider == "aliyun"
        assert result.raw_response == {"key": "val"}


# ============================================================================
# MockOCRProvider 测试
# ============================================================================

class TestMockOCRProvider:
    """MockOCRProvider 测试"""

    def test_provider_name(self):
        """provider_name 返回 'mock'"""
        provider = MockOCRProvider()
        assert provider.provider_name == "mock"

    async def test_extract_returns_result(self):
        """extract 返回 OCRResult 且 provider 为 mock"""
        provider = MockOCRProvider()
        result = await provider.extract("http://example.com/image.png")

        assert isinstance(result, OCRResult)
        assert result.provider == "mock"
        assert result.confidence == 0.95
        assert len(result.text) > 0
        assert "Mock OCR" in result.text

    async def test_extract_text_contains_math_content(self):
        """Mock 文本应包含函数与极限相关内容"""
        provider = MockOCRProvider()
        result = await provider.extract("any_url")
        assert "函数" in result.text or "极限" in result.text


# ============================================================================
# AliyunOCRProvider 测试
# ============================================================================

class TestAliyunOCRProvider:
    """AliyunOCRProvider 测试"""

    def test_provider_name(self):
        """provider_name 返回 'aliyun'"""
        provider = AliyunOCRProvider()
        assert provider.provider_name == "aliyun"

    async def test_extract_parses_aliyun_response(self):
        """正确解析阿里云 OCR 响应格式"""
        provider = AliyunOCRProvider()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "prism_wordsInfo": [
                {"word": "第一行"},
                {"word": "第二行"},
                {"word": ""},  # 空行应被过滤
            ],
            "confidence": 0.92,
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.extract("http://example.com/img.png")

        assert result.provider == "aliyun"
        assert result.text == "第一行\n第二行"
        assert result.confidence == 0.92
        assert result.raw_response is not None

    async def test_extract_raises_on_error(self):
        """API 异常时应抛出"""
        provider = AliyunOCRProvider()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("Network error"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception, match="Network error"):
                await provider.extract("http://example.com/img.png")


# ============================================================================
# TencentOCRProvider 测试
# ============================================================================

class TestTencentOCRProvider:
    """TencentOCRProvider 测试"""

    def test_provider_name(self):
        """provider_name 返回 'tencent'"""
        provider = TencentOCRProvider()
        assert provider.provider_name == "tencent"

    async def test_extract_parses_tencent_response(self):
        """正确解析腾讯云 OCR 响应格式"""
        provider = TencentOCRProvider()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "TextDetections": [
                {"DetectedText": "line one"},
                {"DetectedText": "line two"},
                {"DetectedText": ""},  # 空行过滤
            ],
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.extract("http://example.com/img.png")

        assert result.provider == "tencent"
        assert result.text == "line one\nline two"
        assert result.confidence == 0.9


# ============================================================================
# OCRProviderFactory 测试
# ============================================================================

class TestOCRProviderFactory:
    """OCRProviderFactory 工厂方法测试"""

    def test_factory_returns_mock_when_no_config(self):
        """无任何 API Key 配置时返回 MockOCRProvider"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent,mock"
            mock_settings.ALIYUN_OCR_API_KEY = ""
            mock_settings.TENCENT_OCR_SECRET_ID = ""
            mock_settings.TENCENT_OCR_SECRET_KEY = ""

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, MockOCRProvider)

    def test_factory_returns_aliyun_when_configured(self):
        """配置了阿里云 Key 时返回 AliyunOCRProvider"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent,mock"
            mock_settings.ALIYUN_OCR_API_KEY = "sk-aliyun-real-key"
            mock_settings.TENCENT_OCR_SECRET_ID = ""
            mock_settings.TENCENT_OCR_SECRET_KEY = ""

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, AliyunOCRProvider)

    def test_factory_returns_tencent_when_aliyun_unconfigured(self):
        """阿里云未配置但腾讯云已配置时返回 TencentOCRProvider"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent,mock"
            mock_settings.ALIYUN_OCR_API_KEY = ""
            mock_settings.TENCENT_OCR_SECRET_ID = "tencent-secret-id"
            mock_settings.TENCENT_OCR_SECRET_KEY = "tencent-secret-key"

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, TencentOCRProvider)

    def test_factory_falls_back_to_mock(self):
        """所有 provider 不可用时兜底返回 MockOCRProvider"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            # 只配置了 aliyun 和 tencent，但都没有 Key
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent"
            mock_settings.ALIYUN_OCR_API_KEY = ""
            mock_settings.TENCENT_OCR_SECRET_ID = ""
            mock_settings.TENCENT_OCR_SECRET_KEY = ""

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, MockOCRProvider)

    def test_factory_custom_priority_order(self):
        """自定义优先级链顺序正确"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            # tencent 优先，但 tencent 未配置，aliyun 未配置，mock 兜底
            mock_settings.OCR_PROVIDER_PRIORITY = "tencent,aliyun,mock"
            mock_settings.ALIYUN_OCR_API_KEY = ""
            mock_settings.TENCENT_OCR_SECRET_ID = ""
            mock_settings.TENCENT_OCR_SECRET_KEY = ""

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, MockOCRProvider)

    def test_factory_aliyun_priority_over_tencent(self):
        """阿里云和腾讯云都配置时，优先返回阿里云"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "aliyun,tencent,mock"
            mock_settings.ALIYUN_OCR_API_KEY = "sk-aliyun"
            mock_settings.TENCENT_OCR_SECRET_ID = "tencent-id"
            mock_settings.TENCENT_OCR_SECRET_KEY = "tencent-key"

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, AliyunOCRProvider)

    def test_factory_mock_always_available(self):
        """mock 始终可用（无需配置）"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = "mock"
            mock_settings.ALIYUN_OCR_API_KEY = "sk-aliyun"
            mock_settings.TENCENT_OCR_SECRET_ID = "tencent-id"
            mock_settings.TENCENT_OCR_SECRET_KEY = "tencent-key"

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, MockOCRProvider)

    def test_create_provider_unknown_name_returns_none(self):
        """未知 provider 名称返回 None"""
        result = OCRProviderFactory._create_provider("unknown_provider")
        assert result is None

    def test_create_provider_aliyun_without_key_returns_none(self):
        """阿里云无 Key 时 _create_provider 返回 None"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.ALIYUN_OCR_API_KEY = ""
            result = OCRProviderFactory._create_provider("aliyun")
            assert result is None

    def test_create_provider_tencent_partial_config_returns_none(self):
        """腾讯云只有 SecretID 没有 SecretKey 时返回 None"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.TENCENT_OCR_SECRET_ID = "id-only"
            mock_settings.TENCENT_OCR_SECRET_KEY = ""
            result = OCRProviderFactory._create_provider("tencent")
            assert result is None

    def test_factory_empty_priority_uses_default(self):
        """空优先级字符串时使用默认值"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = ""
            mock_settings.ALIYUN_OCR_API_KEY = ""
            mock_settings.TENCENT_OCR_SECRET_ID = ""
            mock_settings.TENCENT_OCR_SECRET_KEY = ""

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, MockOCRProvider)

    def test_factory_none_priority_uses_default(self):
        """None 优先级时使用默认值"""
        with patch("app.services.ocr_service.settings") as mock_settings:
            mock_settings.OCR_PROVIDER_PRIORITY = None
            mock_settings.ALIYUN_OCR_API_KEY = ""
            mock_settings.TENCENT_OCR_SECRET_ID = ""
            mock_settings.TENCENT_OCR_SECRET_KEY = ""

            provider = OCRProviderFactory.get_provider()
            assert isinstance(provider, MockOCRProvider)
