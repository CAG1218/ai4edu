#!/usr/bin/env python3
"""Check Alembic and DB state on cloud server."""
import paramiko

HOST = "121.43.129.181"
PORT = 22
USER = "root"
PASSWORD = "Team_Shin@2026"

commands = [
    "docker exec ai4edu-backend alembic current 2>&1",
    "docker exec ai4edu-backend alembic history 2>&1 | head -20",
    "docker exec ai4edu-postgres psql -U ai4edu_user -d ai4edu_db -c \"SELECT version_num FROM alembic_version;\" 2>&1 || echo 'alembic_version table missing'",
    "docker exec ai4edu-postgres psql -U ai4edu_user -d ai4edu_db -c \"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;\" 2>&1",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)

try:
    for cmd in commands:
        print(f"\n>>> {cmd[:80]}...")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        if out:
            print(out)
        if err:
            print("STDERR:", err[:500])
finally:
    client.close()
