# Deployment Checklist - Before & After

## ✅ Pre-Deployment Checklist

### 1. Prerequisites
- [ ] AWS Account created
- [ ] IAM permissions verified
- [ ] Credit card/payment method on file
- [ ] Local SSH client installed
- [ ] API Keys obtained:
  - [ ] Google Generative AI (Gemini) Key
  - [ ] Hugging Face API Key

### 2. Repository Preparation
- [ ] Code pushed to GitHub/GitLab
- [ ] `.env.example` file created with placeholders
- [ ] `requirements.txt` is up-to-date
- [ ] `.gitignore` contains `.env` (to avoid exposing keys)
- [ ] README has deployment instructions
- [ ] All scripts have execute permissions locally

### 3. Testing Locally
- [ ] Application runs locally with `python -m uvicorn main:app`
- [ ] All dependencies install without errors
- [ ] Health endpoint works: `curl http://localhost:8000/health`
- [ ] API documentation accessible: `http://localhost:8000/docs`
- [ ] Query endpoint works with sample data
- [ ] File upload tested (if applicable)

### 4. AWS Setup
- [ ] Choose region (recommendations):
  - [ ] `us-east-1` - Northern Virginia (cheapest, most services)
  - [ ] `us-west-2` - Oregon (good for West Coast)
  - [ ] `eu-west-1` - Ireland (good for Europe)
- [ ] Security group rules planned
- [ ] EC2 key pair created and stored safely
- [ ] Instance type selected (t3.micro for testing, t3.small for production)

### 5. Documentation
- [ ] Deployment guide reviewed (AWS_DEPLOYMENT_GUIDE.md)
- [ ] Quick reference saved (QUICK_REFERENCE.md)
- [ ] Domain name (optional) registered or planned
- [ ] Support contacts identified (AWS support plan)

---

## 🚀 Deployment Steps (Checklist)

### Phase 1: EC2 Instance Launch
- [ ] Step 1: Launch EC2 instance from AWS Console
- [ ] Step 2: Configure instance details (1-core, 2GB RAM minimum)
- [ ] Step 3: Add storage (30GB SSD minimum)
- [ ] Step 4: Add security group rules
- [ ] Step 5: Create/download EC2 key pair
- [ ] Step 6: Launch instance
- [ ] Step 7: Note public IP address

### Phase 2: Initial Server Setup
- [ ] SSH into instance successfully
- [ ] System updated: `sudo apt update && sudo apt upgrade -y`
- [ ] Dependencies installed
- [ ] Python 3.12 verified: `python3.12 --version`

### Phase 3: Application Setup
- [ ] Repository cloned from GitHub
- [ ] Virtual environment created
- [ ] Dependencies installed from requirements.txt
- [ ] `.env` file created with real API keys
- [ ] Environment variables verified: `echo $GOOGLE_API_KEY`

### Phase 4: Application Deployment
- [ ] Supervisor configured
- [ ] Supervisor service started and verified
- [ ] Application logs checked for errors
- [ ] Health endpoint responds correctly
- [ ] Nginx configured as reverse proxy
- [ ] Nginx tests pass: `sudo nginx -t`
- [ ] Nginx restarted successfully

### Phase 5: Testing
- [ ] Health check endpoint works
- [ ] Root endpoint returns API info
- [ ] Swagger UI accessible at `/docs`
- [ ] Query endpoint functional
- [ ] File upload endpoint tested (if applicable)
- [ ] Response times acceptable
- [ ] Logs show no errors

### Phase 6: SSL/TLS (Optional but Recommended)
- [ ] Domain name pointing to EC2 IP (if using domain)
- [ ] Certbot installed
- [ ] SSL certificate obtained: `sudo certbot --nginx -d your-domain.com`
- [ ] Certificate auto-renewal enabled
- [ ] HTTPS working and redirects HTTP to HTTPS

### Phase 7: Monitoring Setup
- [ ] Log rotation configured
- [ ] Monitoring tool selected (CloudWatch, New Relic, DataDog)
- [ ] Alerts configured for:
  - [ ] CPU usage > 80%
  - [ ] Memory usage > 85%
  - [ ] Disk space < 5%
  - [ ] Application down
  - [ ] High error rate (>5% errors)
- [ ] Backup script created and tested

---

## 📋 Post-Deployment Checklist

### 1. Immediate (First Hour)
- [ ] All endpoints respond with 200 status
- [ ] No errors in application logs
- [ ] Database connectivity confirmed
- [ ] External API calls working (Google Gemini, HuggingFace)
- [ ] File upload working correctly
- [ ] Performance acceptable (<2s response times)

### 2. First Day
- [ ] Monitor error logs for warnings
- [ ] Check system resources (CPU, memory, disk)
- [ ] Verify auto-restart works (kill process, check restart)
- [ ] Test data persistence (can query previously uploaded files)
- [ ] Load test with multiple concurrent requests
- [ ] Document any issues found

### 3. First Week
- [ ] Monitor trends in error logs
- [ ] Check for memory leaks
- [ ] Verify backup process works
- [ ] Review AWS billing (should be minimal for free tier)
- [ ] Security audit:
  - [ ] SSH key not shared
  - [ ] Environment variables secure
  - [ ] No debug mode enabled in production
  - [ ] CORS properly configured
- [ ] Performance baseline established

### 4. Ongoing Maintenance
- [ ] Weekly backup of Chroma database
- [ ] Monthly security updates: `sudo apt update && sudo apt upgrade`
- [ ] Monthly certificate renewal check (automated but verify)
- [ ] Monitor application logs for patterns
- [ ] Document deployment for team knowledge

---

## 🆘 Common Issues & Quick Fixes

| Issue | Check | Fix |
|-------|-------|-----|
| Port already in use | `sudo lsof -i :8000` | `sudo kill -9 [PID]` or change port |
| Permission denied | File ownership | `sudo chown -R ubuntu:ubuntu /opt/meridian-rag` |
| RAG not initialized | `.env` file | Check API keys are correct |
| 502 Bad Gateway | Gunicorn logs | `tail -f /var/log/fastapi-rag.err.log` |
| High memory usage | Process leak | Restart: `sudo supervisorctl restart fastapi-rag` |
| Slow response times | Database query | Check Chroma DB size: `du -sh ./chroma_db` |
| Git pull fails | Permissions | `sudo chown -R ubuntu:ubuntu /opt/meridian-rag` |
| SSL certificate expires | Certificate check | `sudo certbot certificates` |

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ Application accessible via public IP or domain  
✅ All API endpoints responding with correct status codes  
✅ Health check returns status: "ready"  
✅ Query endpoint returns meaningful results  
✅ File upload and indexing working  
✅ Response times < 2 seconds (average)  
✅ No errors in application logs  
✅ System resources within acceptable ranges  
✅ Auto-restart working after failures  
✅ Backups scheduling and running  

---

## 📊 Performance Targets

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Health endpoint latency | < 500ms | 100-200ms | < 100ms |
| Query latency (avg) | < 3s | 1-2s | < 1s |
| Availability | 99% | 99.5% | 99.9% |
| Error rate | < 1% | < 0.5% | < 0.1% |
| CPU usage | < 70% | 30-50% | 10-20% |
| Memory usage | < 80% | 40-60% | 20-30% |
| Disk usage | < 80% | 30-50% | 10-30% |

---

## 📞 Support & Resources

### Documentation
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn Docs](https://gunicorn.org/)
- [Nginx Docs](https://nginx.org/en/docs/)
- [AWS EC2 Guide](https://docs.aws.amazon.com/ec2/)

### Monitoring Tools
- **AWS CloudWatch** - Free tier: 10 custom metrics
- **New Relic** - Free tier: Basic monitoring
- **Prometheus** - Open source monitoring
- **ELK Stack** - Logs, metrics, analytics

### Community Help
- AWS Forums: https://forums.aws.amazon.com/
- FastAPI Discussions: https://github.com/tiangolo/fastapi/discussions
- Stack Overflow: Tag with `fastapi` and `aws-ec2`

---

## 🔄 Rollback Plan

If issues occur after deployment:

```bash
# Option 1: Restart application
sudo supervisorctl restart fastapi-rag

# Option 2: Stop problematic deployment
sudo supervisorctl stop fastapi-rag
sudo git revert HEAD  # Go back to previous version
sudo supervisorctl start fastapi-rag

# Option 3: Restore from backup
bash backup.sh restore backups/chroma_db_backup_TIMESTAMP.tar.gz

# Option 4: Stop everything and investigate
sudo supervisorctl stop all
sudo systemctl restart nginx
# Check logs and fix issue
sudo supervisorctl start all
```

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**IP Address**: _______________  
**Domain**: _______________  
**Notes**: _______________

