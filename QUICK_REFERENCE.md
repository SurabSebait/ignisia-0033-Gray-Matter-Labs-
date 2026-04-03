# Quick Reference - AWS EC2 Deployment Commands

## 🚀 One-Liner Quick Start

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Run deployment script (does everything automatically)
curl -fsSL https://raw.githubusercontent.com/YOUR-USERNAME/your-repo/main/deploy.sh | bash
```

## 📋 Manual Quick Steps

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv git nginx supervisor

# 2. Clone repo
cd /opt && sudo git clone YOUR-REPO meridian-rag
sudo chown -R ubuntu:ubuntu meridian-rag && cd meridian-rag

# 3. Setup
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
nano .env  # Add your API keys

# 5. Start with supervisor
sudo cp /dev/stdin /etc/supervisor/conf.d/fastapi-rag.conf << 'EOF'
[program:fastapi-rag]
directory=/opt/meridian-rag
command=/opt/meridian-rag/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/fastapi-rag.out.log
stderr_logfile=/var/log/fastapi-rag.err.log
environment=PATH="/opt/meridian-rag/venv/bin"
EOF

sudo supervisorctl reread && sudo supervisorctl update && sudo supervisorctl start fastapi-rag

# 6. Configure Nginx
sudo tee /etc/nginx/sites-available/fastapi-rag > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 100M;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/fastapi-rag /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## 🔍 Monitoring & Debugging

```bash
# Check service status
sudo supervisorctl status fastapi-rag

# View logs in real-time
tail -f /var/log/fastapi-rag.out.log
tail -f /var/log/fastapi-rag.err.log

# View Nginx logs
tail -f /var/log/nginx/access.log

# Check port usage
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep :80

# Restart service
sudo supervisorctl restart fastapi-rag

# Stop service
sudo supervisorctl stop fastapi-rag

# Test endpoint (from EC2)
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Test endpoint (from your local machine)
curl http://your-instance-ip/health
curl http://your-instance-ip/docs
```

## 🔧 Troubleshooting Commands

```bash
# Check if Python venv is active
which python3

# Check installed packages
pip list | grep fastapi

# Test FastAPI app directly (without gunicorn)
cd /opt/meridian-rag && source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Check environment variables
cat /opt/meridian-rag/.env

# Verify API keys are set
grep GOOGLE_API_KEY /opt/meridian-rag/.env
grep HUGGINGFACE_API_KEY /opt/meridian-rag/.env

# Check disk space
df -h

# Check memory usage
free -h

# Check system logs
sudo journalctl -xe
```

## 📊 Performance Monitoring

```bash
# Real-time system monitoring
htop

# Monitor specific process
ps aux | grep gunicorn

# Check CPU usage
top -p $(pgrep -f gunicorn | tr '\n' ',')

# View network connections
sudo ss -tulpn | grep :8000

# Application performance
curl -w "@curl-format.txt" http://your-ip/health
# (See curl-format.txt below)
```

## 📁 File Locations Reference

```bash
# Application directory
/opt/meridian-rag/

# Python environment
/opt/meridian-rag/venv/

# Configuration files
/etc/supervisor/conf.d/fastapi-rag.conf
/etc/nginx/sites-available/fastapi-rag
/opt/meridian-rag/.env

# Log files
/var/log/fastapi-rag.out.log
/var/log/fastapi-rag.err.log
/var/log/nginx/access.log
/var/log/nginx/error.log

# Database
/opt/meridian-rag/chroma_db/

# Uploads
/opt/meridian-rag/temp_uploads/
```

## 🔄 Update Application

```bash
# Pull latest changes
cd /opt/meridian-rag
sudo git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart application
sudo supervisorctl restart fastapi-rag

# Verify update
curl http://your-ip/
```

## 📤 Upload Files for Debugging

```bash
# From your local machine, upload a file to EC2
scp -i your-key.pem local-file.pdf ubuntu@your-instance-ip:/opt/meridian-rag/

# Download logs from EC2
scp -i your-key.pem ubuntu@your-instance-ip:/var/log/fastapi-rag.out.log ./logs/
```

## 🔐 Security Commands

```bash
# Install SSL certificate
sudo certbot --nginx -d your-domain.com

# Check certificate expiry
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --dry-run

# Check firewall rules
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## 🗑️ Cleanup & Maintenance

```bash
# Clear temp uploads
rm -rf /opt/meridian-rag/temp_uploads/*

# Clear supervisor logs
sudo truncate -s 0 /var/log/fastapi-rag.out.log
sudo truncate -s 0 /var/log/fastapi-rag.err.log

# Backup database
tar -czf ~/chroma_db_backup.tar.gz /opt/meridian-rag/chroma_db/

# Clean old backups (keep only last 7)
ls -t /opt/meridian-rag/backups/*.tar.gz | tail -n +8 | xargs rm -f
```

## 🆘 Emergency Kill & Restart

```bash
# Kill all gunicorn processes
pkill -f gunicorn

# Kill service forcefully
sudo supervisorctl stop fastapi-rag
sleep 2
sudo supervisorctl start fastapi-rag

# Check if port is stuck
sudo lsof -i :8000
sudo kill -9 <PID>

# Restart everything
sudo systemctl restart nginx
sudo supervisorctl restart all
```

## 📨 Useful curl Testing

```bash
# Test health endpoint with timing
curl -w "\n%{time_total}s total\n" http://your-ip/health

# Test query with output to file
curl -X POST http://your-ip/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}' \
  -o response.json

# Test with verbose output
curl -v http://your-ip/docs

# Test file upload
curl -X POST http://your-ip/api/ingest \
  -F "files=@policy.pdf" \
  | jq .

# Get response headers only
curl -I http://your-ip/health
```

## 💡 Pro Tips

✅ **Monitor in background**: `nohup tail -f /var/log/fastapi-rag.out.log > monitor.log &`  
✅ **SSH without password**: `ssh-copy-id -i your-key.pem ubuntu@your-instance-ip`  
✅ **Keep SSH session alive**: Add to `~/.ssh/config`:  
```
Host *
  ServerAliveInterval 60
  ServerAliveCountMax 10
```

✅ **Create alias for quick access**:
```bash
alias fastapi-logs='ssh -i ~/key.pem ubuntu@your-ip "tail -f /var/log/fastapi-rag.out.log"'
alias fastapi-status='ssh -i ~/key.pem ubuntu@your-ip "sudo supervisorctl status"'
```

---

**Last Updated**: 2026-04-03  
**FastAPI Version**: 0.115.14  
**Gunicorn Version**: 20.1.0
