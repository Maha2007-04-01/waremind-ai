# 🚀 WareMind AI — Deployment Guide
### Backend → Render | Frontend → Vercel

---

## 📋 TABLE OF CONTENTS
1. [Backend — Render Deployment](#-backend--render-deployment)
2. [Frontend — Vercel Deployment](#-frontend--vercel-deployment)
3. [Environment Variables Reference](#-environment-variables-reference)
4. [Post-Deployment Steps](#-post-deployment-steps)
5. [Local Development Commands](#-local-development-commands)

---

## 🖥️ BACKEND — Render Deployment

### Step 1 — Create a Render Account
Go to → https://render.com → Sign up / Login with GitHub

### Step 2 — Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo: `Maha2007-04-01/waremind-ai`
3. Click **"Connect"**

### Step 3 — Configure the Web Service

| Setting | Value |
|---------|-------|
| **Name** | `waremind-ai-backend` |
| **Region** | Singapore (closest to India) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --workers 2 --bind 0.0.0.0:$PORT "app:create_app()"` |
| **Plan** | Free |

### Step 4 — Set Environment Variables on Render

Go to your service → **"Environment"** tab → Add each variable:

```
SECRET_KEY          = waremind-super-secret-key-2026-render
FLASK_ENV           = production
FLASK_DEBUG         = False
DATABASE_PATH       = /opt/render/project/src/backend/database/waremind.db
CORS_ORIGINS        = https://waremind-ai.vercel.app,https://*.vercel.app
GEMINI_API_KEY      = (paste your real Gemini API key here — optional)
PYTHON_VERSION      = 3.11.0
```

> Replace `waremind-ai.vercel.app` with your actual Vercel URL after deploying frontend.

### Step 5 — Deploy
Click **"Create Web Service"** → Wait 3 minutes for first deploy.

Your backend URL will be:
```
https://waremind-ai-backend.onrender.com
```

---

## 🌐 FRONTEND — Vercel Deployment

### Step 1 — Create a Vercel Account
Go to → https://vercel.com → Sign up / Login with GitHub

### Step 2 — Import Project
1. Click **"Add New..."** → **"Project"**
2. Select repo: `Maha2007-04-01/waremind-ai`
3. Click **"Import"**

### Step 3 — Configure the Project

| Setting | Value |
|---------|-------|
| **Project Name** | `waremind-ai` |
| **Framework Preset** | `Vite` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |
| **Node.js Version** | `20.x` |

### Step 4 — Set Environment Variables on Vercel

Go to project **Settings** → **Environment Variables** → Add:

```
VITE_API_BASE_URL = https://waremind-ai-backend.onrender.com/api
```

> Replace with your actual Render backend URL.

### Step 5 — Deploy
Click **"Deploy"** → Wait ~2 minutes.

Your frontend URL will be:
```
https://waremind-ai.vercel.app
```

---

## 🔑 ENVIRONMENT VARIABLES REFERENCE

### Backend (Render)

| Variable | Example Value | Required |
|----------|--------------|----------|
| `SECRET_KEY` | `waremind-super-secret-key-2026` | YES |
| `FLASK_ENV` | `production` | YES |
| `FLASK_DEBUG` | `False` | YES |
| `DATABASE_PATH` | `/opt/render/project/src/backend/database/waremind.db` | YES |
| `CORS_ORIGINS` | `https://waremind-ai.vercel.app` | YES |
| `PYTHON_VERSION` | `3.11.0` | YES |
| `GEMINI_API_KEY` | `your-gemini-key` | OPTIONAL |

### Frontend (Vercel)

| Variable | Example Value | Required |
|----------|--------------|----------|
| `VITE_API_BASE_URL` | `https://waremind-ai-backend.onrender.com/api` | YES |

---

## POST-DEPLOYMENT STEPS

### 1. Update CORS on Render
After you get your Vercel URL, go to Render → Environment:
```
CORS_ORIGINS = https://YOUR-APP-NAME.vercel.app
```
Click **"Save Changes"** — Render auto-redeploys.

### 2. Update API URL on Vercel
After you get your Render URL, go to Vercel → Settings → Environment Variables:
```
VITE_API_BASE_URL = https://YOUR-RENDER-APP.onrender.com/api
```
Then go to **Deployments** → **Redeploy**.

### 3. Seed the Database (First Time Only)
Open Render **Shell** tab and run:
```bash
python database/seed.py
```

### 4. Test the Live APIs
```
GET  https://waremind-ai-backend.onrender.com/api/health
POST https://waremind-ai-backend.onrender.com/api/auth/login
```

---

## 💻 LOCAL DEVELOPMENT COMMANDS

### Start Backend
```bash
cd "waremind ai/backend"
python app.py
# Runs on: http://localhost:5000
```

### Start Frontend
```bash
cd "waremind ai/frontend"
npm run dev
# Runs on: http://localhost:3000
```

### Run All Tests
```bash
cd "waremind ai"
python -m pytest tests/ -v
```

### Run Auth Tests Only
```bash
python -m pytest tests/test_auth.py -v
```

### Push to GitHub
```bash
cd "waremind ai"
git add .
git commit -m "your message"
git push origin main
```

---

## 🔗 YOUR LIVE LINKS (fill in after deploying)

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://waremind-ai.vercel.app |
| Backend (Render) | https://waremind-ai-backend.onrender.com |
| GitHub Repo | https://github.com/Maha2007-04-01/waremind-ai |
| API Health Check | https://waremind-ai-backend.onrender.com/api/health |

---

## IMPORTANT NOTES

1. **Free Render Tier**: Backend spins down after 15 minutes idle. First request takes ~30s to wake up. Upgrade to Paid ($7/mo) to avoid this.

2. **SQLite on Render**: Free tier has ephemeral storage — DB resets on redeploy. For production, use Render's free PostgreSQL addon.

3. **Never commit `.env`**: Use the platform's Environment Variables UI on Render and Vercel. Your local `.env` is in `.gitignore`.

4. **Gemini API Key**: If your old key was exposed, revoke it at https://console.cloud.google.com → APIs → Credentials.
