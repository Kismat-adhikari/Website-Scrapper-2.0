# Render Deployment Guide

Your web scraper is now ready for Render deployment! 🚀

## Quick Deploy Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Deploy on Render

1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will auto-detect the `render.yaml` configuration

**Or manually configure:**
- **Name**: web-scraper (or your choice)
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: Start with Free tier (can upgrade later)

### 3. Environment Variables (Optional)
Add these in Render dashboard if needed:
- `PYTHON_VERSION`: 3.11.0
- `PLAYWRIGHT_BROWSERS_PATH`: /opt/render/.cache/ms-playwright

### 4. Deploy!
Click "Create Web Service" and Render will:
- Install dependencies
- Install Playwright browser
- Start your Flask app with Gunicorn

## What Changed

✅ Added `gunicorn` to requirements.txt (production WSGI server)
✅ Added `flask` and `flask-cors` to requirements.txt
✅ Updated app.py to use PORT environment variable
✅ Set debug=False for production
✅ Created render.yaml for automatic configuration

## Important Notes

### Free Tier Limitations
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- 750 hours/month free (enough for one service)

### Upgrade for Production
For better performance, upgrade to:
- **Starter ($7/mo)**: Always on, faster CPU
- **Standard ($25/mo)**: More memory for heavy scraping

### Browser Automation on Render
Playwright works on Render but:
- Uses more memory (consider Starter plan minimum)
- Chromium is installed during build
- Headless mode is automatic

### Monitoring
- Check logs in Render dashboard
- Monitor memory usage
- Set up health checks if needed

## Testing After Deploy

Once deployed, test your endpoints:

```bash
# Replace YOUR_APP_URL with your Render URL
curl https://YOUR_APP_URL.onrender.com/

# Test scraping
curl -X POST https://YOUR_APP_URL.onrender.com/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Troubleshooting

### Build Fails
- Check Python version compatibility
- Verify all dependencies in requirements.txt
- Check build logs in Render dashboard

### Memory Issues
- Upgrade to Starter plan ($7/mo)
- Reduce concurrent scraping workers
- Optimize browser pool settings

### Slow Performance
- Free tier spins down - upgrade to Starter
- Add caching for frequently scraped URLs
- Use Redis for session storage (optional)

## Next Steps

1. **Custom Domain**: Add your domain in Render settings
2. **HTTPS**: Automatic with Render
3. **Monitoring**: Set up health checks
4. **Scaling**: Upgrade plan as needed
5. **Database**: Add PostgreSQL if storing results

Your scraper is production-ready! 🎉
