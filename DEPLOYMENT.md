# Department Cup 2026 · Vercel Deployment Guide

This project is fully groomed and optimized for zero-configuration deployment to **Vercel** serverless functions.

---

## 🚀 Quick Deployment Steps

### Step 1: Push Code to GitHub
Ensure all your changes are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Deploy to Vercel"
git push origin main
```

### Step 2: Import Project into Vercel
1. Log in to [vercel.com](https://vercel.com) and click **"Add New..."** → **"Project"**.
2. Select your `department-cup` repository and click **Import**.
3. In **Framework Preset**, keep it as **Other** (Vercel automatically detects `api/index.py` and `vercel.json`).
4. In **Root Directory**, keep it as `./`.

### Step 3: Configure Environment Variables
Before clicking Deploy, expand the **Environment Variables** section and add the following keys:

| Variable | Description | Example / Recommendation |
|---|---|---|
| `MONGO_URI` | MongoDB Atlas connection string | `mongodb+srv://<user>:<pwd>@cluster.mongodb.net/?retryWrites=true&w=majority` |
| `DATABASE_NAME` | MongoDB database name | `department_cup` |
| `SECRET_KEY` | Secret key for signed session cookies | A long random string (e.g. 32+ characters) |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `994308449521-...apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | `GOCSPX-...` |
| `GOOGLE_REDIRECT_URI_AUDIENCE` | OAuth redirect for audience page | `https://<your-project>.vercel.app/` |
| `GOOGLE_REDIRECT_URI_ADMIN` | OAuth redirect for admin console | `https://<your-project>.vercel.app/admin` |

> **Note:** If `GOOGLE_REDIRECT_URI_*` are not explicitly defined, the app automatically constructs them using Vercel's built-in `VERCEL_URL` environment variable.

### Step 4: Add Redirect URIs to Google Cloud Console
For Google Sign-in and Admin authentication to work on your live site:
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Select your OAuth 2.0 Client ID.
3. Under **Authorized JavaScript origins**, add:
   - `https://<your-project>.vercel.app`
4. Under **Authorized redirect URIs**, add:
   - `https://<your-project>.vercel.app/`
   - `https://<your-project>.vercel.app/admin`
5. Click **Save**.

---

## 🏗️ Architecture & Serverless Optimizations

### 1. Zero-Cold-Start Dual Persistence
- Serverless environments have ephemeral filesystems. All match state, squads, tosses, and live commentary are synchronized in real-time to **MongoDB Atlas**.
- Local file cache utilizes `/tmp/department_cup_data` within Lambda warm containers to provide sub-millisecond local reads.

### 2. Real-Time Updates (WebSocket & HTTP Polling Fallback)
- Vercel Serverless Functions do not support long-lived persistent WebSocket connections.
- The frontend client (`base.js`) includes an automatic fallback:
  - Tries WebSocket connection (`/ws/live`).
  - If disconnected or running on serverless, it seamlessly degrades to lightweight HTTP polling (`/api/match/{id}/poll`) every 3 seconds with differential DOM updates.
  - Reactions and comments are transmitted via REST API endpoints (`/api/match/{id}/react`), ensuring 100% functionality without WebSockets.

### 3. Serverless Entry Point
- Entry point is located at `api/index.py` which exports the FastAPI ASGI application instance.
- `vercel.json` rewrites all incoming traffic to `api/index.py` while ensuring static assets and templates are properly bundled.

---

## 🛠️ Managing Administrators

To add or list administrators in MongoDB before or after deployment, you can run locally:

```bash
# List all registered admins
python manage_admins.py list

# Add a new admin email
python manage_admins.py add user@example.com "Full Name"

# Remove an admin
python manage_admins.py remove user@example.com
```
