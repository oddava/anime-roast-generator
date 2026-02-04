# Vercel Deployment Guide

This guide will walk you through deploying the Anime Roast Generator to Vercel.

## Prerequisites

- [Vercel account](https://vercel.com/signup) (free tier works fine)
- [GitHub repository](https://github.com) with your code pushed
- [Upstash account](https://upstash.com) (for Redis rate limiting)
- Google Gemini API key

## Deployment Steps

### 1. Set Up Upstash Redis (for Rate Limiting)

1. Go to [Upstash Console](https://console.upstash.com)
2. Create a new Redis database
3. Copy the `UPSTASH_REDIS_REST_URL` (it looks like: `https://...upstash.io`)
4. Save this URL for later

### 2. Configure Vercel Environment Variables

In your Vercel project dashboard, go to **Settings** → **Environment Variables** and add:

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-lite
FRONTEND_URL=https://your-project-name.vercel.app
UPSTASH_REDIS_URL=your_upstash_redis_url_here
RATE_LIMIT_PER_MINUTE=10
LOG_REQUESTS=true
```

**Note**: Replace `your-project-name` with your actual Vercel project URL.

### 3. Deploy to Vercel

#### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy (from project root)
vercel --prod
```

#### Option B: Using Git Integration

1. Push your code to GitHub
2. Go to [Vercel Dashboard](https://vercel.com/dashboard)
3. Click **Add New Project**
4. Import your GitHub repository
5. Vercel will auto-detect the configuration from `vercel.json`
6. Add the environment variables from Step 2
7. Click **Deploy**

### 4. Verify Deployment

Once deployed, your app will be available at:
- `https://your-project-name.vercel.app`

Test the following:
- [ ] Search for an anime
- [ ] Generate a roast
- [ ] Check that reviews are analyzed
- [ ] Verify rate limiting works
- [ ] Test sharing functionality

## Project Structure for Vercel

```
anime-roast-generator/
├── api/
│   └── index.py              # Vercel serverless entry point
├── backend/                  # FastAPI backend code
│   ├── main.py
│   ├── config.py
│   ├── security.py
│   ├── models.py
│   ├── anilist_client.py
│   └── review_analyzer.py
├── frontend/                 # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── requirements.txt          # Root level dependencies
└── vercel.json              # Vercel configuration
```

## Key Configuration Files

### vercel.json
Routes API requests to the Python backend and serves the frontend:
- `/api/*` → Python backend
- Static files → Frontend build
- SPA fallback → index.html

### api/index.py
Serverless entry point that wraps the FastAPI app with Mangum for AWS Lambda compatibility.

### requirements.txt
Root-level dependencies including:
- FastAPI + Uvicorn
- Google Generative AI
- Mangum (serverless adapter)
- Redis (for Upstash)
- All other backend dependencies

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key |
| `GEMINI_MODEL` | No | Model to use (default: gemini-2.0-flash-lite) |
| `FRONTEND_URL` | Yes | Your Vercel deployment URL |
| `UPSTASH_REDIS_URL` | Yes | Upstash Redis REST URL for rate limiting |
| `RATE_LIMIT_PER_MINUTE` | No | Rate limit per IP (default: 10) |
| `LOG_REQUESTS` | No | Enable request logging (default: true) |

## Troubleshooting

### Issue: API returns 404
**Solution**: Check that `vercel.json` is in the root directory and routes are configured correctly.

### Issue: Rate limiting not working
**Solution**: Verify `UPSTASH_REDIS_URL` is set correctly. Check Upstash dashboard for connection issues.

### Issue: CORS errors
**Solution**: Update `FRONTEND_URL` to match your actual Vercel deployment URL. The config automatically handles preview deployments.

### Issue: Gemini API errors
**Solution**: Verify `GEMINI_API_KEY` is set correctly in Vercel environment variables.

## Post-Deployment Checklist

- [ ] App loads correctly on Vercel URL
- [ ] Can search for anime titles
- [ ] Roast generation works
- [ ] Review analysis displays
- [ ] Share button works
- [ ] History persists in localStorage
- [ ] Rate limiting prevents abuse
- [ ] Footer links work (X/Twitter, GitHub)

## Custom Domain (Optional)

To use a custom domain:
1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions
4. Update `FRONTEND_URL` environment variable

## Support

For issues or questions:
- Check Vercel logs in the dashboard
- Review Upstash Redis metrics
- Test API endpoints directly
- Check browser console for frontend errors

Happy roasting! 🔥
