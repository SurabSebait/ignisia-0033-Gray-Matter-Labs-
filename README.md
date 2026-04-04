# ignisia-0033-Gray-Matter-Labs-
# Meridian Supply Chain Policy RAG Assistant

A full-stack application combining **FastAPI backend** (Vector RAG pipeline) and **Next.js frontend** for querying Meridian policies using retrieval-augmented generation.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Local Development Setup](#local-development-setup)
5. [Running the Application](#running-the-application)
6. [API Documentation](#api-documentation)
7. [Deployment on Vercel](#deployment-on-vercel)
8. [Environment Variables](#environment-variables)
9. [Project Structure](#project-structure)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

This application enables users to ask questions about Meridian Supply Chain policies and receive accurate answers powered by:

- **Vector Embeddings**: BAAI/bge-small-en-v1.5 (384 dimensions)
- **Vector Database**: Chroma (persistent local storage)
- **LLM**: Google Gemini for answer generation
- **Framework**: LangChain for pipeline orchestration

### Key Features

✅ Document ingestion (PDF, DOCX, XLSX, TXT)
✅ Vector-based semantic search
✅ LLM-powered answer generation with source citations
✅ REST API with automatic documentation
✅ Web UI for easy interaction
✅ Pre-embedded vector file updates from AWS

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│          Next.js Frontend (Port 3000)           │
│  - User Interface                               │
│  - Query submission                             │
│  - Results display with citations               │
└──────────────────┬──────────────────────────────┘
                   │ HTTP Requests
                   ▼
┌─────────────────────────────────────────────────┐
│       FastAPI Backend (Port 8000)               │
├─────────────────────────────────────────────────┤
│  Routes:                                        │
│  • GET  /health              - Health check    │
│  • POST /api/query           - Query documents │
│  • POST /api/ingest          - Update vectors  │
│  • GET  /api/stats           - DB statistics   │
│  • GET  /docs                - Swagger UI      │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│      RAG Pipeline (rag_pipeline.py)             │
├─────────────────────────────────────────────────┤
│  • Vector embeddings (HuggingFace)              │
│  • Chroma vector database                       │
│  • Google Gemini LLM                            │
│  • LangChain orchestration                      │
└─────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

### Required Software

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)
- **Text Editor**: VS Code recommended

### Required API Keys

1. **Google Gemini API Key**
   - Visit: https://aistudio.google.com/app/apikeys
   - Create API key
   - Free tier available

2. **HuggingFace API Key** (Optional)
   - Visit: https://huggingface.co/settings/tokens
   - Create token (can use default HuggingFace models)

---

## 🚀 Local Development Setup

### Step 1: Clone Repository

```bash
# Navigate to your desired directory
cd ~/projects

# Clone the repository
git clone https://github.com/YOUR_USERNAME/ignisia-rag.git
cd ignisia-rag
```

### Step 2: Backend Setup (FastAPI)

```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file in project root
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env

# Edit .env with your API keys
# (see Environment Variables section below)
```

### Step 3: Frontend Setup (Next.js)

```bash
# Install Node.js dependencies
npm install

# Or with yarn
yarn install
```

### Step 4: Verify Installation

```bash
# Check Python packages
pip list | grep -E "fastapi|langchain|chromadb"

# Check Node packages
npm list next react

# Test Python
python -c "import fastapi; print(fastapi.__version__)"

# Test Node
node --version
npm --version
```

---

## ▶️ Running the Application

### Option A: Run Both Services Locally

#### Terminal 1 - FastAPI Backend:

```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start FastAPI server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Terminal 2 - Next.js Frontend:

```bash
# From project root (not in venv)
npm run dev

# Or with yarn
yarn dev
```

**Expected output:**
```
> next dev

▲ Next.js 14.0.0
- Local:        http://localhost:3000
- Environments: .env.local

✓ Ready in 3.2s
```

### Option B: Test Backend Endpoints

```bash
# Health check
curl http://localhost:8000/health
54
# Query endpoint (example)
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the ambient pallet storage rate?"}'

# View interactive API docs
# Open: http://localhost:8000/docs
```

---

## 📚 API Documentation

### Health Check
```
GET /health

Response:
{
  "status": "ready",
  "message": "RAG system initialized"
}
```

### Query Documents
```
POST /api/query

Request:
{
  "question": "What is the ambient pallet storage rate?"
}

Response:
{
  "question": "What is the ambient pallet storage rate?",
  "answer": "Based on [SOURCE-1], the ambient pallet storage rate is $X per month...",
  "sources": [
    {
      "label": "[SOURCE-1]",
      "doc_id": "policy.pdf",
      "page_num": 5,
      "score": 0.8234,
      "preview": "Ambient Pallet Storage..."
    }
  ],
  "retrieved": [...]
}
```

### Ingest Vector Files
```
POST /api/ingest

Request: (multipart form-data with files)
files: [metadata.parquet, data.parquet, index.db, ...]

Response:
{
  "status": "success",
  "message": "Successfully wrote 5 file(s) to chroma_db",
  "files_written": 5,
  "destination": "./chroma_db"
}
```

### Get Statistics
```
GET /api/stats

Response:
{
  "total_documents": 1250
}
```

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🌐 Deployment on Vercel

### Backend Deployment (FastAPI on Vercel)

#### Step 1: Create Vercel Account

1. Go to https://vercel.com/signup
2. Sign up with GitHub
3. Authorize Vercel

#### Step 2: Prepare for Vercel Deployment

Create `vercel.json` in project root:

```json
{
  "buildCommand": "pip install -r requirements.txt",
  "devCommand": "uvicorn main:app --reload",
  "env": {
    "GOOGLE_API_KEY": "@google_api_key",
    "HUGGINGFACE_API_KEY": "@huggingface_api_key"
  },
  "functions": {
    "main.py": {
      "runtime": "python3.10"
    }
  }
}
```

Create `requirements.txt` if not exists:

```txt
fastapi==0.104.1
uvicorn==0.24.0
langchain==0.1.16
langchain-core==0.1.42
langchain-google-genai==1.0.0
langchain-community==0.0.17
langchain-chroma==0.1.0
chromadb==0.4.24
python-dotenv==1.0.0
sentence-transformers==2.2.2
google-generativeai==0.3.0
python-multipart==0.0.6
```

#### Step 3: Deploy Backend

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel deploy

# Or deploy with environment variables
vercel env add GOOGLE_API_KEY
vercel env add HUGGINGFACE_API_KEY
vercel deploy --prod
```

**Get your backend URL:**
```
https://your-project-name.vercel.app
```

---

### Frontend Deployment (Next.js on Vercel)

#### Step 1: Configure API Endpoint

In `next.config.js` or `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.vercel.app
```

Update your API calls to use:

```javascript
const response = await fetch(
  `${process.env.NEXT_PUBLIC_API_URL}/api/query`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: userQuery })
  }
);
```

#### Step 2: Deploy Frontend

```bash
# Push to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# Deploy via Vercel dashboard
# 1. Go to https://vercel.com/new
# 2. Import your GitHub repository
# 3. Add environment variables
# 4. Click Deploy
```

**Or via CLI:**

```bash
vercel deploy --prod
```

---

## 🔐 Environment Variables

Create `.env` file in project root:

```env
# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# HuggingFace API (optional)
HUGGINGFACE_API_KEY=your_hf_token_here

# FastAPI Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000  # Local dev
# For production:
# NEXT_PUBLIC_API_URL=https://your-backend-url.vercel.app
```

### Getting API Keys

**Google Gemini:**
1. Visit: https://aistudio.google.com/app/apikeys
2. Click "Create API Key"
3. Copy and paste in `.env`

**HuggingFace:**
1. Visit: https://huggingface.co/settings/tokens
2. Create token with read access
3. Copy and paste in `.env`

---

## 📁 Project Structure

```
ignisia-rag/
├── main.py                 # FastAPI application
├── rag_pipeline.py         # RAG logic
├── system_prompt.txt       # LLM system prompt
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example            # Example environment file
├── .gitignore              # Git ignore rules
│
├── app/                    # Next.js frontend
│   ├── page.tsx            # Main page
│   ├── layout.tsx          # Layout
│   ├── api/                # API routes (if needed)
│   └── components/         # React components
│
├── chroma_db/              # Vector database (local)
│   ├── metadata.parquet
│   ├── data.parquet
│   └── .chroma/
│
├── public/                 # Static files
├── package.json            # Node.js dependencies
├── next.config.js          # Next.js configuration
├── tsconfig.json           # TypeScript configuration
│
├── vercel.json             # Vercel deployment config
└── README.md               # This file
```

---

## 🐛 Troubleshooting

### FastAPI Issues

#### Port 8000 Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

#### Module Not Found Errors

```bash
# Verify virtual environment is activated
which python  # macOS/Linux - should show venv path
where python  # Windows - should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Gemini API Key Invalid

```bash
# Verify key in .env
cat .env | grep GOOGLE_API_KEY

# Test API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

#### Chroma Database Errors

```bash
# Reset database (WARNING: deletes all indexed documents)
rm -rf chroma_db

# Restart backend
python main.py
```

---

### Next.js Issues

#### Port 3000 Already in Use

```bash
# Use different port
npm run dev -- -p 3001
```

#### Module Dependencies Missing

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### API Endpoint Not Responding

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `.env.local` has correct API URL
3. Check browser console for CORS errors
4. Verify FastAPI CORS middleware is enabled in `main.py`

---

### Deployment Issues

#### Vercel Build Fails

```bash
# Check build logs
vercel logs

# Verify all dependencies in requirements.txt
pip freeze > requirements.txt

# Test build locally
vercel build --prod
```

#### Environment Variables Not Set

```bash
# Vercel dashboard → Settings → Environment Variables
# Add:
# GOOGLE_API_KEY = your_key
# HUGGINGFACE_API_KEY = your_key

# Or via CLI
vercel env add GOOGLE_API_KEY
vercel env add HUGGINGFACE_API_KEY
```

#### Vector Database Not Persisting

Vercel has ephemeral storage. For persistent vectors:
- Use AWS S3 bucket for backups
- Implement Lambda function for regular updates
- Update via `/api/ingest` endpoint with backup files

---

## 📞 Support

### Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [Vercel Documentation](https://vercel.com/docs)

### Common Commands

```bash
# Backend development
uvicorn main:app --reload --port 8000

# Frontend development
npm run dev

# Run pytest (if available)
pytest

# Format code
black main.py rag_pipeline.py

# Check code quality
pylint main.py

# Build frontend for production
npm run build
npm start
```

---

## 📝 License

This project is proprietary to Meridian Supply Chain Solutions.

---

## 🔄 Version History

- **v1.0.0** (April 2026): Initial release with FastAPI + Next.js
- Full RAG pipeline with vector embeddings
- Document ingestion and query endpoints
- Vercel deployment support

---

**Last Updated**: April 4, 2026
