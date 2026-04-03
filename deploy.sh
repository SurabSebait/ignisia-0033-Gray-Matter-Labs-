#!/bin/bash
# FastAPI RAG - Quick Deployment Script for AWS EC2
# Run this script with: bash deploy.sh

set -e

echo "🚀 FastAPI RAG EC2 Deployment Script"
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Update System
echo -e "${YELLOW}[1/8]${NC} Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Dependencies
echo -e "${YELLOW}[2/8]${NC} Installing dependencies..."
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    git \
    nginx \
    supervisor \
    curl \
    wget \
    certbot \
    python3-certbot-nginx

# Step 3: Clone Repository
echo -e "${YELLOW}[3/8]${NC} Cloning repository..."
cd /opt
if [ -d "meridian-rag" ]; then
    echo "Repository already exists. Updating..."
    cd meridian-rag
    sudo git pull origin main
else
    echo "Enter your GitHub repository URL (e.g., https://github.com/user/repo.git):"
    read REPO_URL
    sudo git clone $REPO_URL meridian-rag
    cd meridian-rag
fi
sudo chown -R ubuntu:ubuntu /opt/meridian-rag

# Step 4: Create Virtual Environment
echo -e "${YELLOW}[4/8]${NC} Setting up Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Step 5: Setup Environment Variables
echo -e "${YELLOW}[5/8]${NC} Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${RED}⚠️  Please edit .env file with your API keys:${NC}"
    echo "   nano /opt/meridian-rag/.env"
    exit 1
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

# Step 6: Create Supervisor Configuration
echo -e "${YELLOW}[6/8]${NC} Configuring Supervisor..."
sudo tee /etc/supervisor/conf.d/fastapi-rag.conf > /dev/null <<EOF
[program:fastapi-rag]
directory=/opt/meridian-rag
command=/opt/meridian-rag/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/fastapi-rag.err.log
stdout_logfile=/var/log/fastapi-rag.out.log
environment=PATH="/opt/meridian-rag/venv/bin"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fastapi-rag

# Step 7: Configure Nginx
echo -e "${YELLOW}[7/8]${NC} Configuring Nginx..."
echo "Enter your domain name (or press Enter for IP-only access):"
read DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    DOMAIN_NAME="_"
    echo "Using IP-only access (no domain configured)"
else
    echo "Domain set to: $DOMAIN_NAME"
fi

sudo tee /etc/nginx/sites-available/fastapi-rag > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/fastapi-rag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Step 8: SSL Setup (Optional)
echo -e "${YELLOW}[8/8]${NC} SSL Certificate Setup"
if [ ! -z "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "_" ]; then
    read -p "Setup SSL with Let's Encrypt? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo certbot --nginx -d $DOMAIN_NAME
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer
        echo -e "${GREEN}✓ SSL Certificate installed${NC}"
    fi
else
    echo "Skipping SSL (no domain configured)"
fi

# Final Status Check
echo ""
echo -e "${GREEN}===================================="
echo "✓ Deployment Complete!${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo "📋 Next Steps:"
echo "  1. Check application status:"
echo "     sudo supervisorctl status fastapi-rag"
echo ""
echo "  2. View logs:"
echo "     tail -f /var/log/fastapi-rag.out.log"
echo ""
echo "  3. Test health endpoint:"
if [ -z "$DOMAIN_NAME" ] || [ "$DOMAIN_NAME" = "_" ]; then
    echo "     Get your instance public IP from AWS console, then:"
    echo "     curl http://YOUR-IP/health"
else
    echo "     curl http://$DOMAIN_NAME/health"
fi
echo ""
echo "  4. Access API documentation:"
if [ -z "$DOMAIN_NAME" ] || [ "$DOMAIN_NAME" = "_" ]; then
    echo "     http://YOUR-IP/docs"
else
    echo "     http://$DOMAIN_NAME/docs"
fi
echo ""
