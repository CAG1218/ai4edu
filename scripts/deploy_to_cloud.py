#!/usr/bin/env python3
"""Deploy v2 code to Aliyun ECS and restart services."""
import paramiko

HOST = "121.43.129.181"
PORT = 22
USER = "root"
PASSWORD = "Team_Shin@2026"

commands = [
    # Backup existing deployment
    "cd /opt/ai4edu && tar -czf /opt/ai4edu-backup-$(date +%Y%m%d-%H%M%S).tar.gz backend deploy frontend .env README.md overview.md 2>/dev/null || echo 'backup skipped'",
    # Extract new code
    "cd /opt/ai4edu && tar -xzf ai4edu-v2-deploy.tar.gz --overwrite 2>&1",
    # Verify v2 files present
    "ls -la /opt/ai4edu/backend/app/services/ocr_service.py /opt/ai4edu/backend/app/services/quota_manager.py /opt/ai4edu/backend/app/services/agent_export_service.py /opt/ai4edu/backend/app/core/celery_app.py 2>&1",
    # Install new Python deps inside backend container
    "cd /opt/ai4edu && docker exec ai4edu-backend pip install 'reportlab>=4.0' 'celery[redis]>=5.3' 2>&1",
    # Run Alembic migrations
    "cd /opt/ai4edu && docker exec -w /app -e PYTHONPATH=/app ai4edu-backend alembic upgrade head 2>&1",
    # Rebuild backend image
    "cd /opt/ai4edu && docker compose -f deploy/docker-compose.yml build backend --no-cache 2>&1 | tail -20",
    # Recreate backend and celery containers
    "cd /opt/ai4edu && docker compose -f deploy/docker-compose.yml up -d --force-recreate backend celery-worker celery-beat 2>&1",
    # Wait and check status
    "sleep 10 && docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Image}}' 2>&1",
    "docker logs ai4edu-backend --tail 15 2>&1",
    "docker logs ai4edu-celery-worker --tail 20 2>&1",
    "docker logs ai4edu-celery-beat --tail 10 2>&1",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)

try:
    for cmd in commands:
        print(f"\n>>> {cmd[:80]}...")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        if out:
            print(out)
        if err:
            print("STDERR:", err[:500])
finally:
    client.close()

print("\nDeployment commands executed.")
