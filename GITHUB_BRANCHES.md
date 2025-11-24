# GitHub Branch Structure

## Overview
Your web scraper project uses a simple two-branch workflow.

---

## **Branches**

### `main` (Production)
- Stable, tested code
- Latest release version
- Protected branch (merge from `web` after testing)

### `web` (Development)
- Active development branch
- Latest features and fixes
- All work happens here

---

## **Configuration Files**

- `requirements.txt` - Python dependencies
- `requirements_flask.txt` - Flask dependencies
- `proxies.txt` - Proxy list (ip:port format)
- `sample_urls.txt` - Test URLs

---

## **How to Use**

### Clone the repo
```bash
git clone <your-repo-url>
cd <repo-name>
```

### Switch to a branch
```bash
git checkout web    # Development
git checkout main   # Production
```

### Make changes and push
```bash
git checkout web
# Make changes
git add .
git commit -m "feat: description of changes"
git push origin web
```

### Merge to main (when ready for production)
```bash
git checkout main
git pull origin main
git merge web
git push origin main
```

---

## **Branch Status**

| Branch | Status | Purpose |
|--------|--------|---------|
| `main` | Stable | Production release |
| `web` | Active | Development & testing |

---

## **Quick Start**

### Run the scraper (CLI)
```bash
# Single URL
python scraper.py https://example.com

# Multiple URLs from file
python scraper.py sample_urls.txt

# With proxies
python scraper.py sample_urls.txt --proxy-file proxies.txt

# Advanced mode (multi-page, addresses, company info)
python scraper.py sample_urls.txt --threads 10

# Basic mode (emails & phones only)
python scraper.py sample_urls.txt --basic
```

### Run the web API
```bash
python app.py
# Visit http://localhost:5000
```

---

## **What's Included**

### Core Scraper
- ✅ 3 fetch modes with intelligent selection
- ✅ Automatic fallback escalation
- ✅ Proxy rotation and anti-blocking
- ✅ Pre-check system (SSL, bot detection)
- ✅ Page discovery and multi-page scraping
- ✅ Comprehensive logging

### Validation
- ✅ Email syntax validation
- ✅ SMTP verification with connection pooling
- ✅ Phone validation (US/International)
- ✅ Role-based email detection
- ✅ Disposable domain detection
- ✅ MX record verification

### Advanced Features
- ✅ Multi-page parallel scraping
- ✅ Address extraction and parsing
- ✅ Company name/description extraction
- ✅ Data quality scoring
- ✅ Parallel URL processing (up to 150 concurrent)

### Web API
- ✅ Single URL scraping endpoint
- ✅ Batch processing
- ✅ CSV export
- ✅ Email validation endpoint
- ✅ Real-time results
- ✅ Keyword blocking

---

## **Performance Metrics**

- **Single URL**: 7-9 seconds (with optimizations)
- **Batch Processing**: ~8-10 seconds per URL (parallel)
- **Concurrent URLs**: Up to 150 with ThreadPoolExecutor
- **Email Validation**: 0.5-2 seconds per email (SMTP)
- **Phone Validation**: <0.1 seconds per phone

---

## **Workflow**

1. **Work on `web`** - All development happens here
2. **Test thoroughly** - Make sure everything works
3. **Merge to `main`** - When ready for production
4. **Tag releases** - Use semantic versioning (v1.0.0, v1.1.0, etc.)

---

## **Support**

For issues or questions:
1. Review SCRAPER_ANALYSIS.md for architecture details
2. Check VALIDATION_FLOW.md for validation pipeline
3. Review FLASK_README.md for API documentation
4. See COMPLETE_ANALYSIS.md for performance analysis

---

**Last Updated**: November 24, 2025
