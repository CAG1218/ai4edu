# AI 智能体中心 v2 — 交付总览

## TL;DR
完成 AI 智能体中心 4 项增强能力（板书/录播 OCR/ASR 提取、多租户配额计量、对话导出 PDF/MD、模型负载均衡），42 个文件 8384 行代码，179 个测试全部通过，已推送 GitHub。

## 交付概览

| 指标 | 数值 |
|------|------|
| 交付状态 | ✅ 全部完成 |
| 测试通过率 | 179/179 (100%) |
| 已知问题数 | 0 |
| 新增文件 | 26 |
| 修改文件 | 16 |
| 代码行数 | +8384 / -238 |
| Git 提交 | `fddf28d` |
| 分支 | `陈安国的代码——AI智能体中心` |

## 4 项能力实现详情

### 1. 板书/录播自动 OCR/ASR 提取（P1）
- **架构**：Strategy + Factory 设计模式，多 provider 抽象层
- **降级链**：aliyun → tencent → mock（无 API Key 也能跑通）
- **异步处理**：Celery 任务队列（Redis broker）
- **关键文件**：
  - `backend/app/services/ocr_service.py` — OCR 多 provider
  - `backend/app/services/asr_service.py` — ASR 多 provider
  - `backend/app/tasks/extraction_tasks.py` — Celery 异步任务
  - `backend/app/api/v1/classroom.py` — 课堂记录 API
- **测试**：OCR 22 个 + ASR 20 个 = 42 个全部通过

### 2. 多租户模型配额计量（P2）
- **架构**：Redis 实时计数 + DB 持久化日志
- **计数策略**：日配额（TTL 25h）+ 月配额（TTL 35d）
- **关键文件**：
  - `backend/app/services/quota_manager.py` — QuotaManager 单例
  - `backend/app/models/usage.py` — LLMUsageLog + TenantQuota
  - `backend/app/api/v1/quota.py` — 配额管理 API
  - `frontend/src/views/admin/QuotaDashboard.vue` — 配额看板
- **测试**：7 个全部通过

### 3. 对话导出 PDF/Markdown（P2）
- **架构**：reportlab 纯 Python PDF 生成（无系统依赖），MinIO 预签名 URL
- **安全**：导出文件仅创建者可下载，30 分钟有效期
- **关键文件**：
  - `backend/app/services/agent_export_service.py` — 导出服务
  - `backend/app/tasks/export_tasks.py` — Celery 导出任务
  - `backend/app/api/v1/export.py` — 导出 API
  - `frontend/src/components/agent/ExportDialog.vue` — 导出对话框
- **测试**：7 个全部通过

### 4. 模型负载均衡（P2）
- **架构**：基于延迟/可用性的动态负载均衡
- **策略**：latency（默认按延迟排序）、weighted（按成功率加权随机）、sticky（优先 recommended_model）
- **健康指标**：指数移动平均（EMA）更新 avg_latency_ms 和 success_rate
- **关键改造**：
  - `backend/app/agents/llm_router.py` — 新增 tenant_id 配额检查 + 健康指标 + balancer 状态
  - `backend/app/tasks/health_check.py` — Celery beat 每 60s 探测
- **测试**：10 个全部通过

## 数据库变更
- **新增 3 表**：llm_usage_logs、tenant_quotas、agent_exports
- **修改 2 表**：classroom_records（加 file_url/provider/error_msg/updated_at）、teacher_methods（加 recommended_model）
- **迁移文件**：`backend/migrations/versions/c8e2a4f7b901_add_v2_models.py`

## 文档产出
- `docs/prd-ai-agent-center-v2.md` — 增量 PRD（用户故事 + 需求池 + UI 设计 + 流程图）
- `docs/architecture-ai-agent-center-v2.md` — 增量架构设计（10 项设计决策 + 5 个任务分解）
- `docs/class-diagram-v2.mermaid` — v2 类图
- `docs/sequence-diagram-v2.mermaid` — v2 时序图

## SOP 流程
```
产品经理（许清楚）→ PRD v2
    ↓
架构师（高见远）→ 架构设计 v2 + 任务分解
    ↓
工程师（寇豆码）→ 代码实现（42 文件，IS_PASS: YES）
    ↓
QA（严过关）→ 测试验证（179 passed）
    ↓
主理人（齐活林）→ Git commit + push GitHub
```

## 用户下一步建议
1. ~~**运行 Alembic 迁移**~~：✅ 已完成（3 新表 + 2 表加字段）
2. ~~**安装新依赖**~~：✅ 已完成（reportlab + celery[redis]）
3. ~~**启动 Celery worker**~~：✅ 已完成（Docker 容器 ai4edu-celery-worker）
4. ~~**启动 Celery beat**~~：✅ 已完成（Docker 容器 ai4edu-celery-beat，每 60s 健康检查）
5. ~~**重建后端 Docker 容器**~~：✅ 已完成（9 容器全部运行新镜像，v2 API 已上线）
6. **配置 OCR/ASR API Key**（可选）：设置 ALIYUN_OCR_API_KEY / TENCENT_OCR_SECRET_ID 等环境变量，无配置时自动降级为 mock

## 部署修复记录
- `schemas/classroom.py`：合并旧+新 schema（v2 覆盖了旧 ClassroomCreate 等类）
- `api/v1/classroom.py`：修复 `get_db_dep` 未定义 → 改用 `get_db` from `app.dependencies`
- `docker-compose.yml`：修复 celery 模块路径 `app.celery` → `app.core.celery_app` + 补全环境变量
- `.dockerignore`：排除 `celerybeat-schedule*` 文件
- 提交：`a521d1c`

## 当前运行状态
- **9 个 Docker 容器**：backend + celery-worker + celery-beat + postgres + redis + neo4j + clickhouse + elasticsearch + minio
- **Backend API**：http://localhost:8000（Swagger UI: /docs）
- **11 个 v2 API 端点**：balancer / classroom-records / admin/quotas / agents/exports
