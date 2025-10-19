# BuildWise - Production Deployment Guide for Render.com

Complete step-by-step instructions for deploying BuildWise to production on Render.com with PostgreSQL database and persistent storage.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Backend API Deployment](#backend-api-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Environment Variables Reference](#environment-variables-reference)
7. [Troubleshooting](#troubleshooting)
8. [Scaling & Optimization](#scaling--optimization)

---

## Prerequisites

### Required Accounts
- [x] GitHub account (code repository)
- [x] Render.com account (https://render.com/signup)
- [x] Stripe account (for payment processing) - optional initially

### Local Setup
- [x] Git installed and repository pushed to GitHub
- [x] Backend and Frontend code committed
- [ ] Test locally with PostgreSQL (recommended but not required)

---

## Database Setup

### Step 1: Create PostgreSQL Database

1. **Login to Render Dashboard**
   - Navigate to https://dashboard.render.com

2. **Create New PostgreSQL Database**
   - Click **"New +"** → **"PostgreSQL"**
   - Configure:
     - **Name**: `buildwise-db`
     - **Database**: `buildwise_main`
     - **User**: `buildwise_admin` (auto-generated)
     - **Region**: `Frankfurt` (or closest to your users)
     - **PostgreSQL Version**: `15`
     - **Plan**: Start with `Starter` ($7/month)
   - Click **"Create Database"**

3. **Save Connection Details**
   Render will provide:
   - **Internal Database URL**: `postgresql://buildwise_admin:PASSWORD@dpg-xxxxx-a/buildwise_main`
   - **External Database URL**: For external access (if needed)
   - **Hostname**, **Port**, **Database**, **Username**, **Password**

   > **Important**: The Internal Database URL is automatically provided to your services via the `DATABASE_URL` environment variable.

### Step 2: Verify Database Connection (Optional)

Use a PostgreSQL client like `psql` or TablePlus to connect and verify:

```bash
psql postgresql://buildwise_admin:PASSWORD@dpg-xxxxx-a.oregon-postgres.render.com/buildwise_main
```

---

## Backend API Deployment

### Step 1: Prepare Repository

1. **Ensure all files are committed:**
   ```bash
   git add .
   git commit -m "Production deployment configuration"
   git push origin main
   ```

2. **Verify critical files exist:**
   - `render.yaml` ✓
   - `build.sh` ✓
   - `start.sh` ✓
   - `Dockerfile` ✓
   - `requirements.txt` with gunicorn ✓
   - `env.production.example` ✓

### Step 2: Create Persistent Disk

1. **Navigate to "Disks"** in Render Dashboard
2. Click **"New Disk"**
3. Configure:
   - **Name**: `buildwise-storage`
   - **Size**: `1 GB` (increase later if needed)
   - **Region**: `Frankfurt` (same as database)
4. Click **"Create Disk"**

> **Note**: This disk will be mounted at `/var/data` in your backend service.

### Step 3: Deploy Backend Service

#### Option A: Using Blueprint (render.yaml)

1. **Go to Render Dashboard**
2. Click **"New +"** → **"Blueprint"**
3. **Connect your GitHub repository**
4. **Select branch**: `main`
5. **Blueprint file**: `render.yaml` (should be detected automatically)
6. **Review services**:
   - Backend web service: `buildwise-api`
   - Database: `buildwise-db` (will connect automatically)
7. Click **"Apply"**

#### Option B: Manual Setup

1. **Create Web Service**
   - Click **"New +"** → **"Web Service"**
   - Connect GitHub repository
   - Configure:
     - **Name**: `buildwise-api`
     - **Region**: `Frankfurt`
     - **Branch**: `main`
     - **Runtime**: `Python 3`
     - **Build Command**: `bash build.sh`
     - **Start Command**: `bash start.sh`
     - **Plan**: `Starter` ($7/month) or higher

2. **Add Environment Variables** (see [Environment Variables Reference](#environment-variables-reference))

3. **Attach Persistent Disk**
   - In service settings → **"Disks"**
   - Mount `buildwise-storage` at `/var/data`

4. **Connect Database**
   - In service settings → **"Environment"**
   - Add environment variable:
     - Key: `DATABASE_URL`
     - Value: Select from database `buildwise-db` → `Internal Connection String`

### Step 4: Configure Environment Variables

In your backend service settings → **"Environment"**, add:

#### Required Variables:

```bash
# Database (automatically set if using Blueprint)
DATABASE_URL=<from database connection>

# JWT Security (generate secure key!)
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (update after frontend deployment)
ALLOWED_ORIGINS=https://your-frontend.onrender.com
FRONTEND_URL=https://your-frontend.onrender.com

# Environment
ENVIRONMENT=production
DEBUG=false
RENDER=true

# BuildWise Configuration
BUILDWISE_FEE_PERCENTAGE=4.7
BUILDWISE_FEE_PHASE=production
ENVIRONMENT_MODE=production
```

#### Optional but Recommended:

```bash
# Stripe (add later when ready for payments)
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# OAuth (if using Google/Microsoft login)
GOOGLE_CLIENT_ID=xxxxx
GOOGLE_CLIENT_SECRET=xxxxx
MICROSOFT_CLIENT_ID=xxxxx
MICROSOFT_CLIENT_SECRET=xxxxx
```

### Step 5: Deploy and Monitor

1. **Trigger Deployment**
   - Click **"Manual Deploy"** → **"Deploy latest commit"**
   - Or push to `main` branch (auto-deploy if enabled)

2. **Monitor Build Logs**
   - Watch for:
     - ✓ Dependencies installed
     - ✓ Storage directories created
     - ✓ Database migrations ran
     - ✓ Gunicorn started with workers

3. **Check Deployment Status**
   - Service should show **"Live"** status
   - Note your backend URL: `https://buildwise-api.onrender.com`

4. **Test Health Endpoint**
   ```bash
   curl https://buildwise-api.onrender.com/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "service": "BuildWise API",
     "version": "1.0.0"
   }
   ```

---

## Frontend Deployment

### Step 1: Update Frontend Configuration

1. **Create `.env.production` file** (copy from `env.production.example`):
   ```bash
   VITE_API_URL=https://buildwise-api.onrender.com/api/v1
   ```

2. **Commit changes:**
   ```bash
   git add .env.production
   git commit -m "Add production environment config"
   git push origin main
   ```

### Step 2: Deploy Frontend as Static Site

1. **Go to Render Dashboard**
2. Click **"New +"** → **"Static Site"**
3. **Connect GitHub repository** (Frontend folder)
4. Configure:
   - **Name**: `buildwise-frontend`
   - **Branch**: `main`
   - **Root Directory**: `Frontend/Frontend` (adjust to your structure)
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `Frontend/Frontend/dist`
5. **Add Environment Variables**:
   ```bash
   VITE_API_URL=https://buildwise-api.onrender.com/api/v1
   ```
6. Click **"Create Static Site"**

### Step 3: Update Backend CORS Settings

Once frontend is deployed, update backend environment variables:

1. **Get frontend URL**: `https://buildwise-frontend.onrender.com`
2. **Update backend environment variables**:
   ```bash
   ALLOWED_ORIGINS=https://buildwise-frontend.onrender.com
   FRONTEND_URL=https://buildwise-frontend.onrender.com
   ```
3. **Redeploy backend** to apply changes

### Step 4: Update OAuth Redirect URIs (if using)

Update redirect URIs in:
- Google Cloud Console
- Microsoft Azure Portal

New URIs:
```
https://buildwise-frontend.onrender.com/auth/google/callback
https://buildwise-frontend.onrender.com/auth/microsoft/callback
```

---

## Post-Deployment Verification

### Health Checks

1. **Backend Health**:
   ```bash
   curl https://buildwise-api.onrender.com/health
   ```

2. **Frontend Loading**:
   - Open `https://buildwise-frontend.onrender.com`
   - Should load login page

3. **API Documentation**:
   - Visit `https://buildwise-api.onrender.com/docs`
   - Interactive API documentation should load

### Functional Testing

Test critical features:

- [ ] User Registration
- [ ] User Login
- [ ] Project Creation
- [ ] Document Upload
- [ ] Milestone Creation
- [ ] Quote Submission
- [ ] Invoice Generation
- [ ] Notifications

### Database Verification

1. **Check database size** in Render Dashboard
2. **Verify tables created**:
   ```sql
   SELECT tablename FROM pg_tables WHERE schemaname = 'public';
   ```

### Performance Check

1. **Response Times**:
   - Health endpoint: < 100ms
   - Login: < 500ms
   - List endpoints: < 1s

2. **Monitor Metrics** in Render Dashboard:
   - CPU usage
   - Memory usage
   - Request count

---

## Environment Variables Reference

### Backend Service

#### Core Configuration
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✓ | PostgreSQL connection string | Auto-provided by Render |
| `JWT_SECRET_KEY` | ✓ | Secret key for JWT tokens | Generate with secrets.token_urlsafe(32) |
| `JWT_ALGORITHM` | ✓ | JWT algorithm | HS256 |
| `ALLOWED_ORIGINS` | ✓ | CORS allowed origins | https://your-frontend.onrender.com |
| `FRONTEND_URL` | ✓ | Frontend base URL | https://your-frontend.onrender.com |

#### Environment Settings
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ENVIRONMENT` | ✓ | Environment name | production |
| `DEBUG` | ✓ | Debug mode | false |
| `RENDER` | ✓ | Render platform flag | true |

#### BuildWise Configuration
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BUILDWISE_FEE_PERCENTAGE` | ✓ | Platform fee | 4.7 |
| `BUILDWISE_FEE_PHASE` | ✓ | Fee phase | production |
| `ENVIRONMENT_MODE` | ✓ | App mode | production |

#### Payment Processing (Optional)
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `STRIPE_SECRET_KEY` | Optional | Stripe secret key | sk_live_xxxxx |
| `STRIPE_PUBLISHABLE_KEY` | Optional | Stripe publishable key | pk_live_xxxxx |
| `STRIPE_WEBHOOK_SECRET` | Optional | Stripe webhook secret | whsec_xxxxx |

#### OAuth (Optional)
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | Optional | Google OAuth client ID | xxxxx.apps.googleusercontent.com |
| `GOOGLE_CLIENT_SECRET` | Optional | Google OAuth secret | xxxxx |
| `MICROSOFT_CLIENT_ID` | Optional | Microsoft OAuth client ID | xxxxx |
| `MICROSOFT_CLIENT_SECRET` | Optional | Microsoft OAuth secret | xxxxx |

### Frontend Static Site

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_URL` | ✓ | Backend API URL | https://buildwise-api.onrender.com/api/v1 |

---

## Troubleshooting

### Build Failures

**Problem**: Build fails with "command not found"
- **Solution**: Ensure `build.sh` has correct line endings (LF not CRLF)
- Run: `dos2unix build.sh` or check Git settings

**Problem**: Python dependencies fail to install
- **Solution**: Check `requirements.txt` for version conflicts
- Try pinning specific versions

### Database Connection Issues

**Problem**: "could not connect to server"
- **Solution**: Verify `DATABASE_URL` is set correctly
- Check database is in same region as web service

**Problem**: "no pg_hba.conf entry"
- **Solution**: Database may not be ready. Wait 1-2 minutes and redeploy

### File Upload Issues

**Problem**: Files not persisting across deploys
- **Solution**: Verify persistent disk is mounted at `/var/data`
- Check disk has free space in Render Dashboard

**Problem**: "Permission denied" on file write
- **Solution**: Check directory permissions in `build.sh`
- Ensure non-root user has write access

### CORS Errors

**Problem**: Frontend can't connect to backend
- **Solution**: Add frontend URL to `ALLOWED_ORIGINS`
- Format: `https://buildwise-frontend.onrender.com` (no trailing slash)

### Performance Issues

**Problem**: Slow response times
- **Solution**: 
  - Upgrade Render plan (more CPU/RAM)
  - Check database query performance
  - Monitor worker count in logs

**Problem**: "Worker timeout" errors
- **Solution**: Increase `GUNICORN_TIMEOUT` environment variable
- Default is 120s, try 180s for heavy operations

---

## Scaling & Optimization

### When to Scale

Monitor these metrics in Render Dashboard:

- **CPU usage** consistently > 70%
- **Memory usage** consistently > 80%
- **Response times** > 2 seconds
- **Error rate** > 1%

### Scaling Options

#### 1. Vertical Scaling (Upgrade Plan)

**Starter → Standard**:
- 0.5 → 1 CPU
- 512 MB → 2 GB RAM
- Cost: $7 → $25/month
- Workers: 2 → 3 (automatic)

**Standard → Pro**:
- 1 → 2 CPU
- 2 → 4 GB RAM
- Cost: $25 → $85/month
- Workers: 3 → 5 (automatic)

#### 2. Database Scaling

**Starter → Standard**:
- 1 GB storage → 10 GB
- 25 connections → 100 connections
- Cost: $7 → $20/month

#### 3. Storage Scaling

Increase persistent disk size:
- 1 GB → 10 GB → 50 GB
- Cost: +$0.25/GB/month

### Performance Optimization Tips

1. **Enable Database Connection Pooling** (already configured)
2. **Monitor slow queries** in database dashboard
3. **Add database indexes** for frequently queried fields
4. **Implement Redis caching** for read-heavy endpoints (future enhancement)
5. **Use CDN** for static assets (Render provides this automatically)

---

## Security Checklist

- [ ] JWT_SECRET_KEY is strong and random (32+ characters)
- [ ] DEBUG mode is false in production
- [ ] CORS origins are restricted to your actual domains
- [ ] Stripe uses live keys, not test keys
- [ ] OAuth credentials are production values
- [ ] Database user has minimal required permissions
- [ ] Persistent disk has appropriate permissions
- [ ] Environment variables are not committed to Git
- [ ] Regular security updates applied

---

## Monitoring & Maintenance

### Daily Checks
- Service status (should be "Live")
- Error logs (should be minimal)
- Disk usage (should have free space)

### Weekly Checks
- Response time metrics
- Database size growth
- Error rate trends

### Monthly Tasks
- Review and rotate secrets
- Check for dependency updates
- Review access logs
- Optimize database queries

---

## Support & Resources

### Render Documentation
- [First Deploy](https://render.com/docs/your-first-deploy)
- [PostgreSQL](https://render.com/docs/postgresql)
- [Persistent Disks](https://render.com/docs/disks)
- [Environment Variables](https://render.com/docs/environment-variables)

### BuildWise Support
- Check application logs in Render Dashboard
- Review `DEPLOYMENT.md` (this file)
- Check `env.production.example` for configuration reference

---

## Quick Deploy Checklist

Use this checklist for deployments:

### Database Setup
- [ ] PostgreSQL database created
- [ ] Connection details saved

### Backend Deployment
- [ ] Persistent disk created and attached
- [ ] Environment variables configured
- [ ] Build.sh and start.sh are executable
- [ ] Service deployed and showing "Live"
- [ ] Health endpoint responding

### Frontend Deployment
- [ ] .env.production configured with API URL
- [ ] Static site deployed
- [ ] Frontend loading correctly

### Post-Deployment
- [ ] CORS settings updated with frontend URL
- [ ] OAuth redirect URIs updated (if applicable)
- [ ] Critical features tested
- [ ] Monitoring configured

---

## Estimated Costs

### Minimum Production Setup
- **Backend Web Service** (Starter): $7/month
- **PostgreSQL Database** (Starter): $7/month
- **Persistent Disk** (1 GB): $0.25/month
- **Frontend Static Site**: Free
- **Total**: ~$15/month

### Recommended Production Setup
- **Backend Web Service** (Standard): $25/month
- **PostgreSQL Database** (Standard): $20/month
- **Persistent Disk** (10 GB): $2.50/month
- **Frontend Static Site**: Free
- **Total**: ~$50/month

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: 2024  
**For**: BuildWise Production Deployment on Render.com


