# PaaS Deployment Guide

Deploy the BSTT Compliance Dashboard to cloud platforms like Railway, Render, or Fly.io.

## Overview

This guide covers deployment to Platform-as-a-Service (PaaS) providers that offer:
- Managed PostgreSQL databases
- Automatic SSL certificates
- Git-based deployments
- Environment variable management

## Prerequisites

- GitHub repository connected to your PaaS account
- Basic familiarity with the platform's CLI (optional but recommended)

---

## Platform Comparison

| Feature | Railway | Render | Fly.io |
|---------|---------|--------|--------|
| **Free Tier** | $5/month credit | 750 hours/month | 3 shared VMs |
| **PostgreSQL** | Add-on | Managed DB | Fly Postgres |
| **Auto SSL** | Yes | Yes | Yes |
| **Regions** | US, EU | US, EU, Asia | Global (35+) |
| **CLI Required** | No | No | Yes |
| **Deploy Time** | ~2-3 min | ~3-5 min | ~2-3 min |

---

## Railway Deployment

### Step 1: Create Project

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select the `BSTT-Web` repository

### Step 2: Add PostgreSQL Database

1. In your project, click "New" → "Database" → "PostgreSQL"
2. Railway automatically sets `DATABASE_URL`

### Step 3: Configure Backend Service

1. Click on the backend service
2. Go to "Settings" → "Build" and set:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2`

3. Go to "Variables" and add:
```
SECRET_KEY=<generate-a-secure-key>
DEBUG=False
ALLOWED_HOSTS=.railway.app
CORS_ALLOWED_ORIGINS=https://your-frontend-url.railway.app
```

### Step 4: Deploy Frontend (Separate Service)

1. Add another service from the same repo
2. Set Root Directory to `frontend`
3. Set Build Command: `npm install && npm run build`
4. Configure as static site or use nginx

### Step 5: Run Migrations

```bash
# Using Railway CLI
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

Or use the Railway shell in the dashboard.

---

## Render Deployment

### Step 1: Create Blueprint

The `render.yaml` file in the repository defines the infrastructure:

```yaml
services:
  - type: web
    name: bstt-backend
    runtime: docker
    dockerfilePath: ./backend/Dockerfile

databases:
  - name: bstt-db
    plan: free
```

### Step 2: Deploy from Dashboard

1. Go to [render.com](https://render.com) and sign in
2. Click "New" → "Blueprint"
3. Connect your GitHub repo
4. Render automatically detects `render.yaml`
5. Click "Apply"

### Step 3: Configure Environment Variables

In the Render dashboard, add to your backend service:

```
SECRET_KEY=<generate-a-secure-key>
CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com
```

`DATABASE_URL` is automatically set from the database connection.

### Step 4: Run Migrations

```bash
# SSH into the service
render ssh bstt-backend

# Run migrations
python manage.py migrate
python manage.py createsuperuser
```

---

## Fly.io Deployment

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Linux
curl -L https://fly.io/install.sh | sh
```

### Step 2: Login and Initialize

```bash
cd BSTT-Web
fly auth login
fly launch --dockerfile backend/Dockerfile
```

When prompted:
- Choose a unique app name (e.g., `bstt-dashboard`)
- Select region (e.g., `iad` for US East)
- Don't deploy yet (we need to set up the database first)

### Step 3: Create PostgreSQL Database

```bash
fly postgres create --name bstt-db
fly postgres attach bstt-db --app bstt-dashboard
```

This automatically sets `DATABASE_URL` as a secret.

### Step 4: Set Secrets

```bash
fly secrets set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
fly secrets set ALLOWED_HOSTS=".fly.dev"
fly secrets set CORS_ALLOWED_ORIGINS="https://your-frontend.fly.dev"
```

### Step 5: Deploy

```bash
fly deploy
```

### Step 6: Run Migrations

```bash
fly ssh console
python manage.py migrate
python manage.py createsuperuser
```

### Step 7: Deploy Frontend

For the React frontend, create a separate Fly app:

```bash
cd frontend
fly launch --name bstt-frontend
```

Use a simple Dockerfile for static hosting or deploy to a CDN like Cloudflare Pages.

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generate with Django |
| `DEBUG` | Debug mode | `False` for production |
| `DATABASE_URL` | PostgreSQL connection | Auto-set by platform |
| `ALLOWED_HOSTS` | Allowed domain names | `.railway.app` |
| `CORS_ALLOWED_ORIGINS` | Frontend URLs | `https://app.railway.app` |
| `PORT` | Server port | Auto-set by platform |

### Generate Secret Key

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Database Migration from SQLite

If you have existing data in SQLite, you can migrate to PostgreSQL:

### Step 1: Export Data from SQLite

```bash
# In your local development environment
python manage.py dumpdata --natural-foreign --natural-primary -o backup.json
```

### Step 2: Import to PostgreSQL

```bash
# On the PaaS platform (via CLI or shell)
python manage.py loaddata backup.json
```

### Alternative: Use pgloader

```bash
pgloader sqlite:///path/to/db.sqlite3 postgresql://user:pass@host:5432/dbname
```

---

## Frontend Deployment Options

### Option 1: Same Platform (Monorepo)

Deploy frontend as a static site service on the same platform.

### Option 2: Vercel (Recommended for React)

```bash
cd frontend
npm install -g vercel
vercel
```

Set `REACT_APP_API_URL` to your backend URL.

### Option 3: Cloudflare Pages

1. Connect GitHub repo to Cloudflare Pages
2. Set build command: `cd frontend && npm run build`
3. Set output directory: `frontend/build`

### Option 4: Netlify

```bash
cd frontend
npm install -g netlify-cli
netlify deploy --prod
```

---

## Monitoring and Logs

### Railway
```bash
railway logs
```

### Render
View logs in the Render dashboard under your service.

### Fly.io
```bash
fly logs
fly status
```

---

## Scaling

### Railway
Adjust resources in the service settings.

### Render
Upgrade plan or add more instances.

### Fly.io
```bash
# Scale to 2 instances
fly scale count 2

# Increase memory
fly scale memory 512
```

---

## Troubleshooting

### Database Connection Errors

1. Verify `DATABASE_URL` is set correctly
2. Check database is running: `fly postgres list` or platform dashboard
3. Ensure IP allowlist includes your service

### Static Files Not Loading

1. Verify `collectstatic` runs during deployment
2. Check `STATIC_ROOT` and `STATIC_URL` settings
3. For Fly.io, ensure `[[statics]]` is configured in `fly.toml`

### CORS Errors

1. Verify `CORS_ALLOWED_ORIGINS` includes your frontend URL
2. Include both `http://` and `https://` if needed
3. Check for trailing slashes

### Health Check Failures

1. Ensure `/api/health/` endpoint exists and returns 200
2. Increase health check timeout if needed
3. Check application logs for startup errors

---

## Cost Considerations

### Free Tier Limits

| Platform | Compute | Database | Bandwidth |
|----------|---------|----------|-----------|
| Railway | $5 credit/month | 500MB PostgreSQL | 100GB |
| Render | 750 hours/month | 256MB PostgreSQL | 100GB |
| Fly.io | 3 shared VMs | 1GB Postgres (paid) | Unlimited |

### Production Recommendations

For production workloads with ~250K records:
- **Railway**: Starter plan ($20/month)
- **Render**: Standard ($25/month)
- **Fly.io**: 1GB RAM VM (~$10/month) + Postgres ($7/month)

---

## Quick Reference

### Railway
```bash
# Install CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up

# Run command
railway run python manage.py migrate
```

### Render
```bash
# Deploy
git push origin main  # Automatic deployment

# SSH into service
render ssh <service-name>
```

### Fly.io
```bash
# Deploy
fly deploy

# SSH into app
fly ssh console

# View logs
fly logs

# Scale
fly scale count 2
```

---

## Security Checklist

- [ ] `SECRET_KEY` is unique and not in version control
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` is restrictive
- [ ] HTTPS is enforced (automatic on all platforms)
- [ ] Database credentials are in secrets/env vars
- [ ] CORS is configured for specific origins only
- [ ] Admin URL could be changed for security
