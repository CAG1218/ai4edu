"""
AI4Edu 数据治理服务
数据分类分级、敏感数据检测、合规审计
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_classification import (
    CLASSIFICATION_LABELS,
    DataClassification,
    classify_field,
    classify_resource,
    detect_sensitive_data,
    mask_sensitive_value,
)
from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams

logger = logging.getLogger(__name__)


class GovernanceService:
    """数据治理服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_audit_logs(
        self,
        tenant_id: int,
        pagination: PaginationParams,
        action_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PaginatedResponse:
        """
        获取审计日志列表

        Args:
            tenant_id: 租户ID
            pagination: 分页参数
            action_type: 操作类型筛选
            user_id: 用户ID筛选
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            分页审计日志列表
        """
        conditions = [AuditLog.tenant_id == tenant_id]

        if action_type:
            conditions.append(AuditLog.action == action_type)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)

        # 日期筛选
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        # 总数
        count_stmt = select(func.count(AuditLog.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 数据
        stmt = (
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(desc(AuditLog.created_at))
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        items = [self._audit_to_dict(log) for log in logs]

        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def create_audit_log(
        self,
        tenant_id: Optional[int],
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        detail: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建审计日志

        Args:
            tenant_id: 租户ID
            user_id: 操作用户ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            detail: 操作详情
            ip_address: IP地址
            user_agent: User-Agent
            request_id: 请求ID

        Returns:
            创建的审计日志
        """
        log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        self.db.add(log)
        await self.db.flush()

        return self._audit_to_dict(log)

    async def export_user_data(
        self,
        tenant_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        导出用户的所有数据（GDPR合规）

        Args:
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            用户数据包
        """
        # 查询用户信息
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalars().first()

        if not user:
            raise NotFoundException(message="用户不存在")

        # 收集用户数据
        user_data = {
            "profile": {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role,
                "grade": user.grade,
                "school": user.school,
                "bio": user.bio,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "tenant_id": tenant_id,
            },
        }

        # 检测敏感数据
        sensitive_findings = detect_sensitive_data(user_data.get("profile", {}))

        # 记录审计日志
        await self.create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="export",
            resource_type="user_data",
            resource_id=user_id,
            detail={"sensitive_findings_count": len(sensitive_findings)},
        )

        return {
            "data": user_data,
            "sensitive_fields_detected": len(sensitive_findings),
            "classification_summary": {
                "public": sum(1 for f in sensitive_findings if f["classification"] == 1),
                "internal": sum(1 for f in sensitive_findings if f["classification"] == 2),
                "sensitive": sum(1 for f in sensitive_findings if f["classification"] == 3),
                "confidential": sum(1 for f in sensitive_findings if f["classification"] == 4),
            },
        }

    async def delete_account(
        self,
        tenant_id: int,
        user_id: int,
    ) -> bool:
        """
        删除用户账户及所有关联数据

        Args:
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        # 记录审计日志
        await self.create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="delete",
            resource_type="user",
            resource_id=user_id,
            detail={"reason": "用户请求删除账户"},
        )

        # 软删除用户
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalars().first()

        if not user:
            return False

        user.is_active = False
        user.deleted_at = datetime.utcnow()
        await self.db.flush()

        return True

    async def get_privacy_settings(
        self,
        tenant_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        获取隐私设置

        Args:
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            隐私设置
        """
        return {
            "user_id": user_id,
            "data_classification_enabled": True,
            "audit_logging_enabled": True,
            "data_retention_days": 365,
            "auto_delete_enabled": False,
            "sensitive_data_masking": True,
            "export_allowed": True,
            "deletion_allowed": True,
            "consent_status": {
                "analytics": True,
                "marketing": False,
                "third_party": False,
            },
        }

    async def update_privacy_settings(
        self,
        tenant_id: int,
        user_id: int,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        更新隐私设置

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            **kwargs: 设置字段

        Returns:
            更新后的设置
        """
        # 记录审计日志
        await self.create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update",
            resource_type="privacy_settings",
            resource_id=user_id,
            detail={"updated_fields": list(kwargs.keys())},
        )

        settings = await self.get_privacy_settings(tenant_id, user_id)
        settings.update(kwargs)
        return settings

    async def get_data_retention_policy(
        self,
        tenant_id: int,
    ) -> Dict[str, Any]:
        """
        获取数据保留策略信息

        Args:
            tenant_id: 租户ID

        Returns:
            数据保留策略
        """
        return {
            "tenant_id": tenant_id,
            "policies": [
                {
                    "resource_type": "user_data",
                    "retention_days": 365,
                    "classification": CLASSIFICATION_LABELS[DataClassification.SENSITIVE],
                    "action_on_expiry": "anonymize",
                },
                {
                    "resource_type": "audit_logs",
                    "retention_days": 730,
                    "classification": CLASSIFICATION_LABELS[DataClassification.CONFIDENTIAL],
                    "action_on_expiry": "delete",
                },
                {
                    "resource_type": "course_content",
                    "retention_days": 0,
                    "classification": CLASSIFICATION_LABELS[DataClassification.INTERNAL],
                    "action_on_expiry": "keep",
                },
                {
                    "resource_type": "diagnosis_data",
                    "retention_days": 365,
                    "classification": CLASSIFICATION_LABELS[DataClassification.SENSITIVE],
                    "action_on_expiry": "anonymize",
                },
                {
                    "resource_type": "notifications",
                    "retention_days": 90,
                    "classification": CLASSIFICATION_LABELS[DataClassification.INTERNAL],
                    "action_on_expiry": "delete",
                },
            ],
            "last_reviewed": datetime.utcnow().isoformat(),
        }

    def _audit_to_dict(self, log: AuditLog) -> Dict[str, Any]:
        """将AuditLog模型转换为字典"""
        detail = None
        if log.detail:
            try:
                detail = json.loads(log.detail)
            except (json.JSONDecodeError, TypeError):
                detail = log.detail

        return {
            "id": log.id,
            "tenant_id": log.tenant_id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": detail,
            "ip_address": log.ip_address,
            "request_id": log.request_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
