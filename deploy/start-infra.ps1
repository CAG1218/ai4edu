# ai4edu 基础服务启动脚本
# 用法: 在 PowerShell 中执行此脚本
# Set-Location "D:\AI Agent\ai4edu\deploy"
# .\start-infra.ps1

$deployDir = "D:\AI Agent\ai4edu\deploy"
Set-Location $deployDir

Write-Host "=== [1/3] 检查 Docker 状态 ===" -ForegroundColor Cyan
docker info | Select-String "Server Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== [2/3] 拉取镜像（国内镜像加速）===" -ForegroundColor Cyan
$images = @(
    "postgres:16-alpine",
    "redis:7-alpine",
    "neo4j:5.20",
    "clickhouse/clickhouse-server:24.1",
    "elasticsearch:8.13.0",
    "minio/minio:latest"
)
foreach ($img in $images) {
    Write-Host "  Pulling $img ..." -ForegroundColor Yellow
    docker pull $img
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  WARN: $img 拉取失败，将在 docker-compose up 时重试" -ForegroundColor Yellow
    }
}

Write-Host "`n=== [3/3] 启动基础服务 ===" -ForegroundColor Cyan
docker compose -f docker-compose.yml up -d postgres redis neo4j clickhouse elasticsearch minio

Write-Host "`n=== 等待服务健康检查 (30s) ===" -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "`n=== 服务状态 ===" -ForegroundColor Cyan
docker compose -f docker-compose.yml ps

Write-Host "`n=== 健康检查 ===" -ForegroundColor Cyan
$services = @("ai4edu-postgres", "ai4edu-redis", "ai4edu-neo4j", "ai4edu-clickhouse", "ai4edu-elasticsearch", "ai4edu-minio")
foreach ($svc in $services) {
    $status = docker inspect --format='{{.State.Health.Status}}' $svc 2>/dev/null
    if ($status -eq "healthy") {
        Write-Host "  [OK] $svc : healthy" -ForegroundColor Green
    } elseif ($status -eq "starting") {
        Write-Host "  [..] $svc : still starting" -ForegroundColor Yellow
    } else {
        Write-Host "  [!!] $svc : $status" -ForegroundColor Red
    }
}
