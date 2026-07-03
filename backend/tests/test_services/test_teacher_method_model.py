"""
TeacherMethod & ClassroomRecord 数据库模型 CRUD 测试
测试范围：模型字段定义、创建、查询、更新、删除、关联查询
"""
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.teacher_method import ClassroomRecord, TeacherMethod
from app.models.user import User


# ============================================================================
# TeacherMethod 模型测试
# ============================================================================

class TestTeacherMethodCRUD:
    """TeacherMethod CRUD 操作测试"""

    @pytest.mark.asyncio
    async def test_create_teacher_method(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """创建老师方法"""
        method = TeacherMethod(
            tenant_id=test_user.tenant_id,
            teacher_id=test_teacher.id,
            title="二次函数解题法",
            content="先配方再求根，步骤如下：1....",
            method_type="board_note",
            knowledge_points='["二次函数", "配方法"]',
            subject="math",
            is_active=True,
        )
        db_session.add(method)
        await db_session.commit()
        await db_session.refresh(method)

        assert method.id is not None
        assert method.title == "二次函数解题法"
        assert method.method_type == "board_note"
        assert method.subject == "math"
        assert method.is_active is True
        assert method.created_at is not None
        assert method.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_with_all_fields(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """创建包含所有字段的老师方法"""
        method = TeacherMethod(
            tenant_id=test_user.tenant_id,
            teacher_id=test_teacher.id,
            course_id=1,
            classroom_id=1,
            title="力学的受力分析方法",
            content="隔离法与整体法...",
            method_type="video_transcript",
            knowledge_points='["受力分析", "牛顿定律"]',
            source_resource_id=1,
            source_url="https://example.com/video/1",
            subject="physics",
            is_active=True,
        )
        db_session.add(method)
        await db_session.commit()
        await db_session.refresh(method)

        assert method.course_id == 1
        assert method.classroom_id == 1
        assert method.source_resource_id == 1
        assert method.source_url == "https://example.com/video/1"

    @pytest.mark.asyncio
    async def test_read_teacher_method(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """查询老师方法"""
        method = TeacherMethod(
            tenant_id=test_user.tenant_id,
            teacher_id=test_teacher.id,
            title="英语阅读理解技巧",
            content="先看题目再看文章...",
            method_type="textbook_solution",
            subject="english",
            is_active=True,
        )
        db_session.add(method)
        await db_session.commit()
        await db_session.refresh(method)

        # 按 ID 查询
        stmt = select(TeacherMethod).where(TeacherMethod.id == method.id)
        result = await db_session.execute(stmt)
        found = result.scalars().first()

        assert found is not None
        assert found.title == "英语阅读理解技巧"
        assert found.subject == "english"

    @pytest.mark.asyncio
    async def test_update_teacher_method(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """更新老师方法"""
        method = TeacherMethod(
            tenant_id=test_user.tenant_id,
            teacher_id=test_teacher.id,
            title="原始标题",
            content="原始内容",
            method_type="manual",
            subject="math",
            is_active=True,
        )
        db_session.add(method)
        await db_session.commit()
        await db_session.refresh(method)

        method.title = "更新后的标题"
        method.content = "更新后的内容"
        method.is_active = False
        await db_session.commit()
        await db_session.refresh(method)

        assert method.title == "更新后的标题"
        assert method.content == "更新后的内容"
        assert method.is_active is False

    @pytest.mark.asyncio
    async def test_delete_teacher_method(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """删除老师方法"""
        method = TeacherMethod(
            tenant_id=test_user.tenant_id,
            teacher_id=test_teacher.id,
            title="待删除",
            content="内容",
            method_type="manual",
            subject="math",
            is_active=True,
        )
        db_session.add(method)
        await db_session.commit()
        await db_session.refresh(method)

        method_id = method.id
        await db_session.delete(method)
        await db_session.commit()

        stmt = select(TeacherMethod).where(TeacherMethod.id == method_id)
        result = await db_session.execute(stmt)
        assert result.scalars().first() is None

    @pytest.mark.asyncio
    async def test_query_by_tenant(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """按租户查询老师方法"""
        for i in range(3):
            method = TeacherMethod(
                tenant_id=test_user.tenant_id,
                teacher_id=test_teacher.id,
                title=f"方法{i}",
                content=f"内容{i}",
                method_type="manual",
                subject="math",
                is_active=True,
            )
            db_session.add(method)
        await db_session.commit()

        stmt = select(TeacherMethod).where(
            TeacherMethod.tenant_id == test_user.tenant_id
        )
        result = await db_session.execute(stmt)
        methods = result.scalars().all()

        assert len(methods) == 3

    @pytest.mark.asyncio
    async def test_query_active_only(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """只查询启用的老师方法"""
        m1 = TeacherMethod(
            tenant_id=test_user.tenant_id, teacher_id=test_teacher.id,
            title="活跃", content="c", method_type="manual", subject="math", is_active=True,
        )
        m2 = TeacherMethod(
            tenant_id=test_user.tenant_id, teacher_id=test_teacher.id,
            title="禁用", content="c", method_type="manual", subject="math", is_active=False,
        )
        db_session.add_all([m1, m2])
        await db_session.commit()

        stmt = select(TeacherMethod).where(
            TeacherMethod.tenant_id == test_user.tenant_id,
            TeacherMethod.is_active == True,  # noqa: E712
        )
        result = await db_session.execute(stmt)
        methods = result.scalars().all()

        assert len(methods) == 1
        assert methods[0].title == "活跃"

    @pytest.mark.asyncio
    async def test_query_by_subject(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """按学科查询"""
        m1 = TeacherMethod(
            tenant_id=test_user.tenant_id, teacher_id=test_teacher.id,
            title="数学方法", content="c", method_type="manual", subject="math", is_active=True,
        )
        m2 = TeacherMethod(
            tenant_id=test_user.tenant_id, teacher_id=test_teacher.id,
            title="物理方法", content="c", method_type="manual", subject="physics", is_active=True,
        )
        db_session.add_all([m1, m2])
        await db_session.commit()

        stmt = select(TeacherMethod).where(TeacherMethod.subject == "physics")
        result = await db_session.execute(stmt)
        methods = result.scalars().all()

        assert len(methods) == 1
        assert methods[0].title == "物理方法"

    @pytest.mark.asyncio
    async def test_optional_fields_default_null(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """可选字段默认为 None"""
        method = TeacherMethod(
            tenant_id=test_user.tenant_id,
            teacher_id=test_teacher.id,
            title="测试",
            content="内容",
            method_type="manual",
            subject="math",
        )
        db_session.add(method)
        await db_session.commit()
        await db_session.refresh(method)

        assert method.course_id is None
        assert method.classroom_id is None
        assert method.knowledge_points is None
        assert method.source_resource_id is None
        assert method.source_url is None

    @pytest.mark.asyncio
    async def test_method_type_values(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """测试各种 method_type 值"""
        valid_types = ["board_note", "video_transcript", "textbook_solution", "manual"]
        for mt in valid_types:
            method = TeacherMethod(
                tenant_id=test_user.tenant_id,
                teacher_id=test_teacher.id,
                title=f"类型_{mt}",
                content="内容",
                method_type=mt,
                subject="math",
                is_active=True,
            )
            db_session.add(method)
        await db_session.commit()

        stmt = select(TeacherMethod).where(
            TeacherMethod.tenant_id == test_user.tenant_id
        )
        result = await db_session.execute(stmt)
        methods = result.scalars().all()

        assert len(methods) == len(valid_types)
        types_in_db = {m.method_type for m in methods}
        assert types_in_db == set(valid_types)


# ============================================================================
# ClassroomRecord 模型测试
# ============================================================================

class TestClassroomRecordCRUD:
    """ClassroomRecord CRUD 操作测试"""

    @pytest.mark.asyncio
    async def test_create_classroom_record(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """创建课堂记录"""
        record = ClassroomRecord(
            tenant_id=test_user.tenant_id,
            classroom_id=1,
            course_id=1,
            record_type="video",
            transcript="老师讲了二次函数...",
            segments='[{"start": 0, "end": 30, "text": "intro"}]',
            knowledge_points='["二次函数"]',
            status="ready",
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        assert record.id is not None
        assert record.record_type == "video"
        assert record.status == "ready"
        assert record.transcript is not None
        assert record.created_at is not None

    @pytest.mark.asyncio
    async def test_classroom_record_default_status(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """课堂记录默认状态为 pending"""
        record = ClassroomRecord(
            tenant_id=test_user.tenant_id,
            classroom_id=1,
            course_id=1,
            record_type="board_photo",
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        assert record.status == "pending"

    @pytest.mark.asyncio
    async def test_classroom_record_optional_fields(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """课堂记录可选字段"""
        record = ClassroomRecord(
            tenant_id=test_user.tenant_id,
            classroom_id=1,
            course_id=1,
            record_type="transcript",
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        assert record.resource_id is None
        assert record.transcript is None
        assert record.segments is None
        assert record.knowledge_points is None

    @pytest.mark.asyncio
    async def test_classroom_record_status_values(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试各种状态值"""
        valid_statuses = ["pending", "processing", "ready", "failed"]
        for i, status in enumerate(valid_statuses):
            record = ClassroomRecord(
                tenant_id=test_user.tenant_id,
                classroom_id=i + 1,
                course_id=1,
                record_type="video",
                status=status,
            )
            db_session.add(record)
        await db_session.commit()

        stmt = select(ClassroomRecord).where(
            ClassroomRecord.tenant_id == test_user.tenant_id
        )
        result = await db_session.execute(stmt)
        records = result.scalars().all()

        assert len(records) == len(valid_statuses)
        statuses_in_db = {r.status for r in records}
        assert statuses_in_db == set(valid_statuses)
