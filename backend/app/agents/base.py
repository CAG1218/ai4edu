"""
AI4Edu Agent 基类
定义智能体公共接口：execute / stream_execute / system_prompt
支持同步和流式输出
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    智能体基类

    所有具体Agent继承此类，实现 system_prompt 属性。
    提供 execute（同步）和 stream_execute（流式）两种调用方式。
    """

    agent_type: str = "base"

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """获取智能体的系统提示词"""
        ...

    def _build_messages(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        """
        构建发送给LLM的消息列表，在开头插入系统提示词

        Args:
            messages: 用户对话消息列表，每条 {role, content}
            context: 上下文信息（user_id, tenant_id, session_id等）

        Returns:
            包含系统提示词的完整消息列表
        """
        system_content = self.system_prompt

        # 如果有上下文信息，追加到系统提示词
        if context:
            context_summary = self._summarize_context(context)
            if context_summary:
                system_content += f"\n\n当前上下文：\n{context_summary}"

        full_messages = [{"role": "system", "content": system_content}]
        full_messages.extend(messages)
        return full_messages

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """将上下文信息汇总为自然语言描述"""
        parts: List[str] = []
        if context.get("user_id"):
            parts.append(f"用户ID: {context['user_id']}")
        if context.get("tenant_id"):
            parts.append(f"租户ID: {context['tenant_id']}")
        if context.get("session_id"):
            parts.append(f"会话ID: {context['session_id']}")
        if context.get("course_id"):
            parts.append(f"课程ID: {context['course_id']}")
        if context.get("scene_type"):
            parts.append(f"场景: {context['scene_type']}")
        if context.get("subject"):
            parts.append(f"学科: {context['subject']}")
        if context.get("grade"):
            parts.append(f"年级: {context['grade']}")
        return "；".join(parts)

    async def execute(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        同步执行：调用LLM获取完整回复

        Args:
            messages: 对话消息列表
            context: 上下文信息

        Returns:
            包含回复内容和元数据的字典
        """
        full_messages = self._build_messages(messages, context)

        try:
            result = await self._call_llm(full_messages)
            return {
                "content": result.get("content", ""),
                "agent_type": self.agent_type,
                "model": result.get("model", settings.OPENAI_MODEL),
                "tokens": result.get("usage", {}),
            }
        except Exception as e:
            logger.error(f"Agent {self.agent_type} 执行失败: {e}")
            return {
                "content": f"抱歉，处理您的请求时出现了问题，请稍后重试。",
                "agent_type": self.agent_type,
                "model": "",
                "tokens": {},
                "error": str(e),
            }

    async def stream_execute(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式执行：逐步yield LLM的输出token

        Args:
            messages: 对话消息列表
            context: 上下文信息

        Yields:
            每个输出token片段
        """
        full_messages = self._build_messages(messages, context)

        if not settings.OPENAI_API_KEY:
            # 无API Key时回退为同步执行
            result = await self.execute(messages, context)
            yield result.get("content", "")
            return

        url = f"{settings.OPENAI_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": full_messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", url, headers=headers, json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Agent {self.agent_type} 流式执行失败: {e}")
            yield "抱歉，处理您的请求时出现了问题，请稍后重试。"

    def _demo_reply(self, messages: List[Dict[str, str]]) -> str:
        """
        无 API Key 时的演示模式回复（基于关键词规则）
        确保 Demo 场景下学伴功能可正常展示。
        """
        import random

        # 获取最后一条用户消息
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "").strip()
                break

        # 从系统提示词判断人设
        system_content = ""
        for m in messages:
            if m.get("role") == "system":
                system_content = m.get("content", "")
                break
        is_humorous = "幽默" in system_content
        is_strict = "严谨" in system_content
        is_gentle = "温柔" in system_content

        def style(text: str) -> str:
            if is_humorous:
                return text + " 😄（以上来自你的幽默学伴，学习要快乐哦！）"
            if is_strict:
                return text + "（严格要求自己，才能走向卓越。）"
            if is_gentle:
                return text + " 慢慢来，你理解了吗？"
            return text + " 💪 我陪着你，一起加油！"

        # 关键词规则匹配
        kw = user_msg.lower()

        if any(w in kw for w in ["学习计划", "计划", "安排", "时间表"]):
            return style(
                "好的！给你规划今日学习计划：\n"
                "① 9:00-9:30  复习昨天的知识点（30分钟）\n"
                "② 9:30-10:20 学习新内容（50分钟）\n"
                "③ 10:20-10:30 小休息☕\n"
                "④ 10:30-11:00 做练习题巩固（30分钟）\n"
                "⑤ 晚上 整理笔记（15分钟）\n"
                "记住：番茄工作法是学习利器，25分钟专注+5分钟休息！"
            )

        if any(w in kw for w in ["不会", "不懂", "困难", "难", "搞不懂", "看不懂"]):
            return style(
                "遇到困难很正常，这是学习的必经之路！让我们拆解一下：\n"
                "1️⃣ 先把问题用自己的话描述一遍\n"
                "2️⃣ 找出哪个具体环节卡住了\n"
                "3️⃣ 查阅教材或笔记中的相关基础\n"
                "4️⃣ 尝试举一个具体的小例子来理解\n"
                "你愿意告诉我具体卡在哪里了吗？我们一起分析！"
            )

        if any(w in kw for w in ["鼓励", "加油", "坚持", "放弃", "累", "烦"]):
            encouragements = [
                "学习的路上总有坎坷，但每一次坚持都是成长！你已经很棒了，继续向前！",
                "积跬步以至千里，积小流以成江海。你每天的努力都在积累！",
                "今天的辛苦是明天的底气。你现在的坚持，未来的你一定会感谢你！",
                "学习不是短跑，是马拉松。保持稳定的节奏比冲刺更重要。你做得很好！",
            ]
            return style(random.choice(encouragements))

        if any(w in kw for w in ["数学", "函数", "方程", "几何", "导数", "积分"]):
            return style(
                "数学是思维的体操！学好数学的关键：\n"
                "🔑 理解概念：不要死记公式，理解背后的逻辑\n"
                "🔑 多做例题：见过的题型越多，解题思路越清晰\n"
                "🔑 整理错题：错题本是提分神器\n"
                "🔑 画图辅助：遇到复杂问题，先画图\n"
                "具体是哪个数学知识点呢？告诉我，我们一起来看看！"
            )

        if any(w in kw for w in ["物理", "力学", "电学", "牛顿", "速度", "加速度"]):
            return style(
                "物理是理解世界的钥匙！学好物理的方法：\n"
                "🔑 建立物理模型：把实际问题抽象成模型\n"
                "🔑 受力分析：每道题先画受力图\n"
                "🔑 公式不要死背：理解物理量之间的关系\n"
                "🔑 多做实验题：培养物理直觉\n"
                "遇到具体问题可以告诉我哦！"
            )

        if any(w in kw for w in ["英语", "单词", "语法", "阅读", "听力", "口语"]):
            return style(
                "英语学习贵在坚持每天积累！推荐方法：\n"
                "📚 单词：用艾宾浩斯遗忘曲线复习，每天20个新词\n"
                "📚 语法：从句型分析入手，不要孤立记规则\n"
                "📚 阅读：精读+泛读结合，遇到生词先猜意思\n"
                "📚 听力：每天听15分钟原声材料\n"
                "语言学习最重要的是开口说！不要怕犯错 😊"
            )

        if any(w in kw for w in ["方法", "技巧", "高效", "效率"]):
            return style(
                "推荐给你几个超实用的学习方法：\n"
                "🍅 番茄工作法：25分钟专注+5分钟休息\n"
                "🧠 费曼学习法：能把知识讲给别人听，才算真正掌握\n"
                "📝 思维导图：整理知识结构，看清全局\n"
                "🔄 间隔重复：合理安排复习间隔，对抗遗忘\n"
                "📖 主动回忆：合上书本，尝试回忆刚学的内容\n"
                "试试看哪个最适合你？"
            )

        if any(w in kw for w in ["笔记", "记笔记", "整理"]):
            return style(
                "好的笔记方法能事半功倍！试试康奈尔笔记法：\n"
                "📝 右侧主栏（70%）：记录课堂内容、关键点\n"
                "📝 左侧线索栏（25%）：课后写关键词、问题\n"
                "📝 底部总结栏（5%）：用自己的话总结本页核心\n"
                "课后要及时回顾整理，趁记忆新鲜补充细节！"
            )

        if any(w in kw for w in ["考试", "测验", "期末", "复习"]):
            return style(
                "考试来袭！制定备考策略：\n"
                "① 梳理考试范围，制作思维导图\n"
                "② 优先复习薄弱知识点\n"
                "③ 做历年真题，了解出题风格\n"
                "④ 注意：考前不要熬夜，睡眠是最好的复习!\n"
                "⑤ 考试时先做有把握的题，最后攻难题\n"
                "你有多久考试？我们来规划一下！"
            )

        if any(w in kw for w in ["你好", "hi", "hello", "嗨", "在吗"]):
            greetings = [
                "你好呀！我是你的AI学伴，很高兴认识你！今天打算学什么呢？😊",
                "嗨！我在哦！有什么我可以帮你的吗？学习问题、方法建议都可以聊！",
                "你好！今天学习状态怎么样？有什么想聊的吗？",
            ]
            return random.choice(greetings)

        # 默认回复
        default_replies = [
            "我听到你说的了！学习过程中有什么具体问题可以跟我详细说说，我会尽力帮你分析和引导的。",
            "这是个好问题！你目前的思路是什么？先说说你的想法，我们一起讨论。",
            "我明白你的意思。学习就是不断探索的过程，遇到困惑很正常。你最想突破的是哪个方向？",
            "好的！无论是学科问题还是学习方法，我都在这里陪你。具体说说看？",
        ]
        return style(random.choice(default_replies))

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        调用 OpenAI 兼容的 LLM API

        Args:
            messages: 消息列表（含系统提示词）
            temperature: 生成温度
            max_tokens: 最大生成token数

        Returns:
            LLM响应结果
        """
        if not settings.OPENAI_API_KEY:
            # Demo 模式：基于规则引擎给出有意义的回复
            demo_content = self._demo_reply(messages)
            return {
                "content": demo_content,
                "model": "demo-rule-engine",
                "usage": {},
            }

        url = f"{settings.OPENAI_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return {
            "content": content,
            "model": data.get("model", settings.OPENAI_MODEL),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }
