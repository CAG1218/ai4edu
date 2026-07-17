"""Create random demo students and enroll them in teacher-owned courses."""

import argparse
import asyncio
import random
import secrets
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.database import async_session_factory
from app.models.course import Course, CourseEnrollment
from app.models.user import User


SURNAMES = ["陈", "林", "周", "吴", "郑", "王", "李", "赵", "孙", "徐", "何", "高"]
GIVEN_NAMES = ["晨曦", "子涵", "思远", "雨桐", "明宇", "欣怡", "嘉诚", "若溪", "浩然", "诗涵", "俊杰", "语彤"]
GRADES = ["大一", "大二", "大三"]
MAJORS = ["数学与应用数学", "物理学", "计算机科学", "化学", "生物科学", "汉语言文学"]
SCHOOLS = ["AI4Edu示范大学", "未来教育学院", "智慧学习实验学校"]
DEFAULT_PASSWORD = "Demo@2026"


async def seed(count: int, teacher_email: str, password: str) -> list[dict]:
    async with async_session_factory() as session:
        teacher = (
            await session.execute(
                select(User).where(User.email == teacher_email, User.deleted_at.is_(None))
            )
        ).scalars().first()
        if not teacher or not teacher.tenant_id:
            raise RuntimeError(f"Teacher not found or has no tenant: {teacher_email}")

        courses = (
            await session.execute(
                select(Course)
                .where(
                    Course.tenant_id == teacher.tenant_id,
                    Course.teacher_id == teacher.id,
                    Course.is_active.is_(True),
                )
                .order_by(Course.id)
            )
        ).scalars().all()
        if not courses:
            raise RuntimeError("The target teacher has no active courses")

        created: list[dict] = []
        used_names: set[str] = set()
        for _ in range(count):
            name = ""
            while not name or name in used_names:
                name = f"{random.choice(SURNAMES)}{random.choice(GIVEN_NAMES)}"
            used_names.add(name)
            token = secrets.token_hex(4)
            email = f"demo.student.{token}@example.com"
            grade = random.choice(GRADES)
            major = random.choice(MAJORS)
            school = random.choice(SCHOOLS)

            student = User(
                tenant_id=teacher.tenant_id,
                email=email,
                password_hash=hash_password(password),
                nickname=name,
                role="student",
                grade=grade,
                school=school,
                major=major,
                bio="教师评价与成长档案功能演示学生",
                default_scene="classroom",
                locale="zh-CN",
                timezone="Asia/Shanghai",
                onboarding_completed=True,
                is_active=True,
            )
            session.add(student)
            await session.flush()

            enrollment_count = random.randint(min(3, len(courses)), min(6, len(courses)))
            selected_courses = random.sample(courses, enrollment_count)
            for course in selected_courses:
                session.add(
                    CourseEnrollment(
                        course_id=course.id,
                        user_id=student.id,
                        role="student",
                        progress=round(random.uniform(8, 88), 1),
                    )
                )

            created.append(
                {
                    "id": student.id,
                    "name": name,
                    "email": email,
                    "password": password,
                    "grade": grade,
                    "major": major,
                    "school": school,
                    "courses": [course.name for course in selected_courses],
                }
            )

        await session.commit()
        return created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=6)
    parser.add_argument("--teacher-email", default="admin@ai4edu.com")
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()
    if not 1 <= args.count <= 50:
        raise ValueError("count must be between 1 and 50")

    students = asyncio.run(seed(args.count, args.teacher_email, args.password))
    for student in students:
        print(
            "|".join(
                [
                    str(student["id"]),
                    student["name"],
                    student["email"],
                    student["password"],
                    student["grade"],
                    student["major"],
                    student["school"],
                    "、".join(student["courses"]),
                ]
            )
        )


if __name__ == "__main__":
    main()
