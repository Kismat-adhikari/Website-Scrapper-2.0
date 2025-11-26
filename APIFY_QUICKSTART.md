# Apify Quick Start Guide

## Prerequisites

1. **Apify Account** - Sign up at https://apify.com (free tier available)
2. **Apify CLI** - Install with `npm install -g apify-cli`
3. **Python 3.11+** - For local testing

## Local Testing

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Create Test Input

Create `input.json`:
```json
{
  "urls": [
    "https://example.com",
    "https://github.com"
  ],
  "fastMode": true,
  "maxPages": 1,
  "maxConcurrency": 2
}
```

### 3. Run Locally

```bash
# Using Python directly
python main.py

# Using Apify CLI (simulates cloud environment)
apify run
```

### 4. Check Results

Results are saved to `apify_storage/datasets/default/`

## Deploy to Apify

### 1. Login to Apify

```bash
apify login
```

### 2. Initialize Actor (if not done)

```bash
apify init
```

### 3. Push to Apify

```bash
apify push
```

This will:
- Build Docker image
- Upload to Apify platform
- Make it available in your account

### 4. Run on Apify

Go to https://console.apify.com and:
1. Find your actor
2. Click "Try it"
3. Enter URLs
4. Click "Start"
5. Download results as CSV/JSON/Excel

## Configuration

### Input Options

```json
{
  "startUrls": [
    { "url": "https://example.com" }
  ],
  "fastMode": true,
  "maxPages": 3,
  "maxConcurrency": 5,
  "enableValidation": false,
  "blockKeywords": "noreply,spam",
  "proxyConfiguration": {
    "useApifyProxy": true
  }
}
```

### Proxy Setup

For best results, enable Apify proxy:
```json
{
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"]
  }
}
```

Cost: ~$0.50 per GB (but much better success rate)

## Performance Tuning

### Fast Scraping (Default)
```json
{
  "fastMode": true,
  "maxPages": 1,
  "maxConcurrency": 10
}
```
- Speed: 1-2s per URL
- Best for: Simple sites

### Thorough Scraping
```json
{
  "fastMode": false,
  "maxPages": 5,
  "maxConcurrency": 3,
  "enableValidation": true
}
```
- Speed: 5-10s per URL
- Best for: JS-heavy sites, high accuracy needed

### Batch Processing
```json
{
  "urls": ["url1", "url2", "..."],
  "maxConcurrency": 20
}
```
- Process 20 URLs in parallel
- Good for large lists

## Monitoring

### Check Logs

In Apify console:
1. Go to your actor run
2. Click "Log" tab
3. See real-time progress

### Check Results

1. Click "Dataset" tab
2. Preview results
3. Download as CSV/JSON/Excel

### Check Costs

1. Go to "Usage" tab
2. See compute units used
3. See proxy bandwidth used

## Troubleshooting

### Actor Fails to Start

**Error**: `Module not found`

**Solution**: Make sure all dependencies are in `requirements.txt`

### No Results Found

**Possible causes**:
1. Site uses JavaScript → Set `fastMode: false`
2. Site blocks scrapers → Enable Apify proxy
3. No contact info on homepage → Increase `maxPages`

### Timeout Errors

**Solution**: Reduce `maxConcurrency` or increase timeout in code

### High Costs

**Tips**:
1. Use `fastMode: true` (faster = cheaper)
2. Reduce `maxPages` (fewer pages = cheaper)
3. Disable `enableValidation` (faster = cheaper)
4. Use datacenter proxy instead of residential

## Cost Estimation

### Compute Units
- 1 URL (fast mode): ~0.001 CU
- 1 URL (browser mode): ~0.005 CU
- 1000 URLs: ~1-5 CU
- Cost: $0.25 per CU

### Proxy Bandwidth
- 1 URL: ~100KB
- 1000 URLs: ~100MB
- Cost: ~$0.50 per GB (residential)

### Example Costs
- 1000 URLs (fast mode, no proxy): ~$0.25
- 1000 URLs (fast mode, with proxy): ~$0.30
- 1000 URLs (browser mode, with proxy): ~$1.50

## Best Practices

1. **Start Small** - Test with 10 URLs first
2. **Use Proxy** - Better success rate, worth the cost
3. **Monitor Logs** - Check for errors early
4. **Batch Process** - Process in batches of 100-500
5. **Cache Results** - Apify caches for 7 days by default

## Next Steps

1. Test locally with `apify run`
2. Push to Apify with `apify push`
3. Run on Apify platform
4. Schedule runs (daily/weekly)
5. Integrate with webhooks/API

## Support

- Apify Docs: https://docs.apify.com
- Apify Discord: https://discord.gg/jyEM2PRvMU
- Actor Issues: GitHub issues

## Version

1.0.0 - Initial Apify release
