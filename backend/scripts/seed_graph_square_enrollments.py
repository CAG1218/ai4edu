"""Create enrolled-course data from the knowledge graph square subjects.

The script is idempotent: it reuses an active course with the same subject and
does not create duplicate enrollment records for the target user.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import async_session_factory
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.services.graph_service import SUBJECT_CATEGORIES


COURSE_SCHEDULES = {
    "math": {
        "location": "博学楼 A201",
        "weekday": "周一",
        "start_time": "08:00",
        "end_time": "09:40",
        "weeks": "第1-16周",
    },
    "physics": {
        "location": "理科楼 B202",
        "weekday": "周一",
        "start_time": "10:00",
        "end_time": "11:40",
        "weeks": "第1-16周",
    },
    "chemistry": {
        "location": "实验楼 C301",
        "weekday": "周二",
        "start_time": "08:00",
        "end_time": "09:40",
        "weeks": "第1-16周",
    },
    "biology": {
        "location": "生命科学楼 D204",
        "weekday": "周二",
        "start_time": "10:00",
        "end_time": "11:40",
        "weeks": "第1-16周",
    },
    "cs": {
        "location": "信息楼 E305",
        "weekday": "周三",
        "start_time": "08:00",
        "end_time": "09:40",
        "weeks": "第1-16周",
    },
    "chinese": {
        "location": "文科楼 F201",
        "weekday": "周三",
        "start_time": "10:00",
        "end_time": "11:40",
        "weeks": "第1-16周",
    },
    "english": {
        "location": "外语楼 G203",
        "weekday": "周四",
        "start_time": "08:00",
        "end_time": "09:40",
        "weeks": "第1-16周",
    },
    "history": {
        "location": "人文楼 H202",
        "weekday": "周四",
        "start_time": "10:00",
        "end_time": "11:40",
        "weeks": "第1-16周",
    },
    "geography": {
        "location": "地学楼 I301",
        "weekday": "周五",
        "start_time": "08:00",
        "end_time": "09:40",
        "weeks": "第1-16周",
    },
    "politics": {
        "location": "社科楼 J204",
        "weekday": "周五",
        "start_time": "10:00",
        "end_time": "11:40",
        "weeks": "第1-16周",
    },
    "pe": {
        "location": "体育馆 1号场",
        "weekday": "周六",
        "start_time": "08:00",
        "end_time": "09:40",
        "weeks": "第1-16周",
    },
    "art": {
        "location": "艺术楼 K201",
        "weekday": "周六",
        "start_time": "10:00",
        "end_time": "11:40",
        "weeks": "第1-16周",
    },
}


def parse_settings(raw_settings: str | None) -> dict:
    if not raw_settings:
        return {}
    try:
        parsed = json.loads(raw_settings)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


async def seed(email: str) -> None:
    async with async_session_factory() as session:
        user = (
            await session.execute(
                select(User).where(User.email == email, User.deleted_at.is_(None))
            )
        ).scalars().first()
        if not user:
            raise RuntimeError(f"User not found: {email}")
        if not user.tenant_id:
            raise RuntimeError(f"User has no tenant: {email}")

        created_courses = 0
        updated_courses = 0
        created_enrollments = 0
        restored_enrollments = 0

        for index, subject in enumerate(SUBJECT_CATEGORIES, start=1):
            subject_id = subject["id"]
            course = (
                await session.execute(
                    select(Course)
                    .where(
                        Course.tenant_id == user.tenant_id,
                        Course.subject == subject_id,
                        Course.is_active.is_(True),
                    )
                    .order_by(Course.id)
                )
            ).scalars().first()

            if not course:
                course = Course(
                    tenant_id=user.tenant_id,
                    name=subject["name"],
                    code=f"GRAPH-{subject_id.upper()}",
                    subject=subject_id,
                    grade="通识",
                    semester="2026-fall",
                    description=f"与知识图谱广场“{subject['name']}”关联的课程",
                    teacher_id=user.id,
                    is_active=True,
                )
                session.add(course)
                await session.flush()
                created_courses += 1

            settings = parse_settings(course.settings)
            settings.update(COURSE_SCHEDULES[subject_id])
            course.settings = json.dumps(settings, ensure_ascii=False)
            if not course.code:
                course.code = f"GRAPH-{subject_id.upper()}"
            updated_courses += 1

            enrollments = (
                await session.execute(
                    select(CourseEnrollment)
                    .where(
                        CourseEnrollment.course_id == course.id,
                        CourseEnrollment.user_id == user.id,
                    )
                    .order_by(CourseEnrollment.id)
                )
            ).scalars().all()

            if not enrollments:
                session.add(
                    CourseEnrollment(
                        course_id=course.id,
                        user_id=user.id,
                        role="student",
                        progress=0.0,
                    )
                )
                created_enrollments += 1
            elif enrollments[0].dropped_at is not None:
                enrollments[0].dropped_at = None
                restored_enrollments += 1

        await session.commit()
        print(
            "Seed complete: "
            f"subjects={len(SUBJECT_CATEGORIES)}, "
            f"courses_created={created_courses}, "
            f"courses_updated={updated_courses}, "
            f"enrollments_created={created_enrollments}, "
            f"enrollments_restored={restored_enrollments}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="admin@ai4edu.com")
    args = parser.parse_args()
    asyncio.run(seed(args.email))


if __name__ == "__main__":
    main()
