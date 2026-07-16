#!/usr/bin/env python3
"""Upload deployment archive to Aliyun ECS via SFTP."""
import os
import sys
import paramiko

HOST = "121.43.129.181"
PORT = 22
USER = "root"
PASSWORD = "Team_Shin@2026"
LOCAL_PATH = r"D:\AI Agent\ai4edu\ai4edu-v2-deploy.tar.gz"
REMOTE_PATH = "/opt/ai4edu/ai4edu-v2-deploy.tar.gz"

if not os.path.exists(LOCAL_PATH):
    print(f"Local archive not found: {LOCAL_PATH}")
    sys.exit(1)

print(f"Connecting to {HOST}:{PORT} as {USER}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)

# Ensure remote directory exists
stdin, stdout, stderr = client.exec_command("mkdir -p /opt/ai4edu && ls -lh /opt/ai4edu")
print(stdout.read().decode(errors="ignore"))

print(f"Uploading {LOCAL_PATH} -> {REMOTE_PATH} ({os.path.getsize(LOCAL_PATH)/1024:.1f} KB)...")
sftp = client.open_sftp()
sftp.put(LOCAL_PATH, REMOTE_PATH)
sftp.close()

stdin, stdout, stderr = client.exec_command(f"ls -lh {REMOTE_PATH}")
print(stdout.read().decode(errors="ignore"))

client.close()
print("Upload complete.")
