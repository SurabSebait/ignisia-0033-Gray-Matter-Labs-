# Alternative: SystemD Service Setup

If you prefer using systemd instead of supervisor, follow these steps:

## Step 1: Create SystemD Service File

```bash
sudo nano /etc/systemd/system/fastapi-rag.service
```

Paste this content:

```ini
[Unit]
Description=FastAPI RAG Application
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/meridian-rag
Environment="PATH=/opt/meridian-rag/venv/bin"
EnvironmentFile=/opt/meridian-rag/.env
ExecStart=/opt/meridian-rag/venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    --timeout 120 \
    main:app

# Auto-restart
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fastapi-rag

[Install]
WantedBy=multi-user.target
```

## Step 2: Enable and Start

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable to start on boot
sudo systemctl enable fastapi-rag

# Start service
sudo systemctl start fastapi-rag

# Check status
sudo systemctl status fastapi-rag

# View logs
sudo journalctl -u fastapi-rag -f
```

## Step 3: Manage Service

```bash
# Stop
sudo systemctl stop fastapi-rag

# Restart
sudo systemctl restart fastapi-rag

# Check recent logs
sudo journalctl -u fastapi-rag -n 50

# Follow logs in real-time
sudo journalctl -u fastapi-rag -f

# Check if service is active
sudo systemctl is-active fastapi-rag
```

## Advantages over Supervisor

✅ Standard Linux practice (no extra packages needed)  
✅ Better logs integration with systemd journal  
✅ Native service management with systemctl  
✅ Auto-restart on system reboot  
✅ Built-in health checks  

## Comparison

| Feature | Supervisor | SystemD |
|---------|-----------|---------|
| Memory Used | ~50MB | Minimal |
| Setup | Easy | Very Easy |
| Built-in | No (extra package) | Yes |
| Log Integration | Separate files | Journald |
| Process Groups | Yes | Limited |
| Production Ready | Yes | Yes |

**Recommendation**: Use systemd for AWS EC2 (simpler, less overhead).
