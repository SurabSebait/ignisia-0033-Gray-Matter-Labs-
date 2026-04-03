# FastAPI RAG Deployment to AWS EC2

This guide walks through deploying your FastAPI endpoint to an AWS EC2 instance.

## Prerequisites

- AWS Account with EC2 access
- SSH client (PuTTY on Windows or PowerShell with SSH)
- Your application files and `.env` file with API keys

## Step 1: Launch EC2 Instance

### 1.1 - Create Instance
1. Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
2. Click "Launch Instance"
3. **Choose AMI**: Select `Ubuntu Server 24.04 LTS` (free tier eligible)
4. **Instance Type**: `t3.micro` or `t3.small` (depending on load)
5. **Storage**: 30 GB (default is fine)
6. **Security Group**: Create new with rules:
   - SSH (port 22) - from your IP
   - HTTP (port 80) - from anywhere (0.0.0.0/0)
   - HTTPS (port 443) - from anywhere (0.0.0.0/0)
   - Custom TCP (port 8000) - from anywhere (for testing)

### 1.2 - Key Pair
- Create/download a `.pem` file
- Store it securely locally
- On Windows: Right-click Properties → Security → Remove inheritance → Grant only your user access

---

## Step 2: Connect to EC2 Instance

```bash
# From PowerShell on Windows
$KeyPath = "C:\path\to\your-key.pem"
$InstanceIP = "your-instance-public-ip"

# Convert PEM to PPK for PuTTY (if needed)
# Or use SSH directly (Windows 10+):
  ssh -i $KeyPath ubuntu@$InstanceIP
```

---

## Step 3: Set Up Server

### 3.1 - Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y git nginx supervisor curl wget
```

### 3.2 - Clone Repository
```bash
cd /opt
sudo git clone https://github.com/YOUR-USERNAME/your-repo.git meridian-rag
  sudo chown -R ubuntu:ubuntu meridian-rag
cd meridian-rag
```

### 3.3 - Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn python-dotenv pydantic numpy chromadb langchain-core langchain-google-genai langchain-chroma langchain-community langchain-text-splitters huggingface_hub openpyxl python-docx PyMuPDF google-generativeai starlette python-multipart requests gunicorn uvicorn sentence-transformers

# Verify FastAPI is installed
pip list | grep -i fastapi
```

### 3.4 - Set Environment Variables
```bash
# Create .env file
nano .env

# Add your keys:
GOOGLE_API_KEY=your-google-api-key-here
HUGGINGFACE_API_KEY=your-huggingface-api-key-here
```

---

## Step 4: Deploy with Gunicorn & Supervisor

### 4.1 - Create Supervisor Configuration
```bash
sudo nano /etc/supervisor/conf.d/fastapi-rag.conf
```

Paste this content:
```ini
[program:fastapi-rag]
directory=/opt/meridian-rag
command=/opt/meridian-rag/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/fastapi-rag.err.log
stdout_logfile=/var/log/fastapi-rag.out.log
environment=PATH="/opt/meridian-rag/venv/bin"
```

### 4.2 - Start Supervisor
```bash
sudo supervisorctl reread
  sudo supervisorctl update
sudo supervisorctl start fastapi-rag
  sudo supervisorctl status
```

Check logs:
```bash
tail -f /var/log/fastapi-rag.out.log
tail -f /var/log/fastapi-rag.err.log
```

---

## Step 5: Configure Nginx Reverse Proxy

### 5.1 - Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/fastapi-rag
```

Paste this content:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this to your domain

    client_max_body_size 100M;    # Allow large file uploads

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### 5.2 - Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/fastapi-rag /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx config
sudo nginx -t

# Restart Nginx
  sudo systemctl restart nginx
```

---

## Step 6: SSL Certificate with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renew (runs automatically every 12 hours)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Step 7: Monitor & Manage

### Check Application Status
```bash
# Application logs
  sudo supervisorctl status fastapi-rag
tail -f /var/log/fastapi-rag.out.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System resources
htop
```

### Auto-Restart on Crash
```bash
# Already configured in supervisor conf (autorestart=true)
# Logs retained for debugging
```

### Update Application
```bash
cd /opt/meridian-rag
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Restart
sudo supervisorctl restart fastapi-rag
```

---

## Step 8: Testing

### Test Health Endpoint
```bash
# From local machine
curl -X GET http://your-ip-or-domain/health

# Expected response:
# {"status": "ready", "message": "RAG system initialized"}
```

### Test Query Endpoint
```bash
curl -X POST http://your-ip-or-domain/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the ambient pallet storage rate?"}'
```

### Test File Upload
```bash
curl -X POST http://your-ip-or-domain/api/ingest \
  -F "files=@/path/to/policy.pdf"
```

---

## Step 9: Optional - Docker Deployment

If you prefer containerized deployment, see `Dockerfile` in the repo.

```bash
# Build image
docker build -t meridian-rag:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your-key \
  -e HUGGINGFACE_API_KEY=your-key \
  -v ./chroma_db:/app/chroma_db \
  meridian-rag:latest
```

---

## Troubleshooting

### Issue: "RAG System not initialized"
**Solution**: Check `.env` file has correct API keys
```bash
cat /opt/meridian-rag/.env
```

### Issue: Port 8000 already in use
**Solution**: Kill existing process
```bash
sudo netstat -tulpn | grep :8000
sudo kill -9 [PID]
```

### Issue: Permission denied errors
**Solution**: Fix permissions
```bash
sudo chown -R ubuntu:ubuntu /opt/meridian-rag
sudo chmod -R 755 /opt/meridian-rag
```

### Issue: Out of memory
**Solution**: Increase swap or reduce worker count in supervisor config
```bash
# Reduce workers from 4 to 2
sudo nano /etc/supervisor/conf.d/fastapi-rag.conf
# Change: -w 2
sudo supervisorctl restart fastapi-rag
```

---

## Architecture Diagram

```
┌──────────────────────┐
│   Internet/Users     │
└──────────┬───────────┘
           │ (HTTPS:443 / HTTP:80)
           ▼
┌──────────────────────┐
│   Nginx Proxy        │
│  (Reverse Proxy)     │
└──────────┬───────────┘
           │ (127.0.0.1:8000)
           ▼
┌──────────────────────┐
│   Gunicorn+Uvicorn   │
│  (4 Workers)         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   FastAPI App        │
│  ├─ /api/query       │
│  ├─ /api/ingest      │
│  └─ /health          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   RAG Pipeline       │
│  ├─ Chroma Vector DB │
│  ├─ Google Gemini    │
│  └─ Embeddings       │
└──────────────────────┘
```

---

## Cost Estimation (AWS Free Tier)

- **EC2 t3.micro**: Free (12 months)
- **Data Transfer**: First 15 GB free/month
- **Storage**: Small Chroma DB fits in 30GB free tier
- **Total Cost**: $0 in first year (t3.micro), ~$8-15/month after

---

## Next Steps

1. ✅ Launch EC2 instance
2. ✅ SSH into instance  
3. ✅ Run all setup steps above
4. ✅ Test endpoints from terminal
5. ✅ Access via browser at `http://your-ip/docs`
6. ✅ Add custom domain (optional)
7. ✅ Set up SSL with Let's Encrypt
8. ✅ Configure monitoring/alerts

---

## Support & References

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [Gunicorn Configuration](https://gunicorn.org/source/stable/configuration.html)
- [Nginx Documentation](https://nginx.org/en/docs/)

