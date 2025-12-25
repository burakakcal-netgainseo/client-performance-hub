# Railway Deployment Guide for Client Performance Hub

## Step 1: Create GitHub Repository (Manual)

1. Go to: https://github.com/new
2. Log in with your credentials
3. Repository settings:
   - **Name:** `client-performance-hub`
   - **Description:** Client Performance Hub - Automated lead tracking and performance monitoring dashboard
   - **Visibility:** Public (or Private if you prefer)
   - **DO NOT** check "Initialize with README" (we already have one)
4. Click **"Create repository"**

## Step 2: Push Code to GitHub

After creating the repository, run these commands in your terminal:

```bash
cd c:\Users\burak\.gemini\antigravity\scratch\client_performance_hub

# Add the remote repository (replace with your actual repo URL)
git remote add origin https://github.com/burakakcal-netgainseo/client-performance-hub.git

# Push to GitHub
git branch -M main
git push -u origin main
```

When prompted for credentials:
- Username: `burakakcal-netgainseo`
- Password: Use a **Personal Access Token** (not your password)

### Creating a Personal Access Token (if needed):
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "Railway Deployment"
4. Select scopes: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token** and use it as your password when pushing

## Step 3: Deploy to Railway

1. Go to: https://railway.app/
2. Click **"Start a New Project"**
3. Choose **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select the `client-performance-hub` repository
6. Railway will automatically detect the `Procfile` and deploy

## Step 4: Configure Environment (if needed)

In Railway dashboard:
1. Click on your deployed service
2. Go to **"Variables"** tab
3. Add any environment variables if needed (currently none required for dashboard-only mode)

## Step 5: Access Your Dashboard

1. Railway will provide a public URL (e.g., `https://client-performance-hub-production.up.railway.app`)
2. Click the URL to access your dashboard
3. Share this URL with your colleagues!

## Important Notes

### Files NOT Pushed to GitHub (Protected):
- `config.py` - Your Gmail credentials
- `service_account.json` - Google service account
- `clients.json` - Client data
- `agent_log.txt` - Logs

These are excluded via `.gitignore` for security.

### What IS Deployed:
- Dashboard web interface (client management)
- HTML templates
- Static assets (logos)
- All Python code except sensitive configs

### What's NOT Deployed (Runs Locally):
- The lead processing agent (`main.py`)
- Email fetching and processing
- Google Sheets integration

The dashboard is read-only for viewing/managing clients. The actual lead processing still runs on your local machine with your credentials.

## Troubleshooting

**If git push fails with authentication error:**
- Use a Personal Access Token instead of password
- Or use SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

**If Railway deployment fails:**
- Check the build logs in Railway dashboard
- Ensure `requirements.txt` includes all dependencies
- Verify `Procfile` is in the root directory

## Next Steps

After deployment, you can:
1. Add a custom domain in Railway settings
2. Enable HTTPS (automatic with Railway)
3. Share the URL with colleagues
4. Monitor usage in Railway dashboard
