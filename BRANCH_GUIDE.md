# Branch Guide - Web Scraper Project

## Branch Structure

This project has two branches optimized for different use cases:

### 🌐 `web` Branch - Flask Development Version

**Purpose**: Local development, testing, and demos with web UI

**What's included**:
- ✅ Flask web interface (`app.py`)
- ✅ Beautiful dark-themed UI (`static/`, `templates/`)
- ✅ Redis queue system (`queue_manager.py`, `tasks.py`)
- ✅ Celery workers for background processing
- ✅ All test files
- ✅ Terminal scraper (`fast_scrape.py`)
- ✅ Complete documentation

**How to use**:
```bash
git checkout web
python app.py
# Open http://localhost:5000
```

**Best for**:
- Local development
- Testing new features
- Demos and presentations
- Quick scraping with UI

---

### 🚀 `main` Branch - Apify Production Version

**Purpose**: Cloud deployment on Apify platform

**What's included**:
- ✅ Apify actor (`main.py`)
- ✅ Apify configuration (`.actor/`)
- ✅ Docker setup for cloud
- ✅ Core scraper modules (shared with web branch)
- ✅ Terminal scraper (`fast_scrape.py`)
- ✅ Apify documentation

**How to use**:
```bash
git checkout main
apify run          # Test locally
apify push         # Deploy to Apify
```

**Best for**:
- Production deployment
- Scaling to thousands of URLs
- Scheduled runs
- API integration

---

## Shared Components

Both branches share the core scraping logic:

- `scraper.py` - Main scraper engine
- `async_scraper.py` - Async HTTP scraper
- `aggressive_scraper.py` - Fallback scraper
- `phone_validator.py` - Phone validation
- `email_validator.py` - Email validation
- `phone_cleaner.py` - Phone cleaning
- `advanced_scraper_features.py` - Company/address extraction
- `context_extractor.py` - Context-aware extraction
- `schema_extractor.py` - Schema.org extraction
- `cache.py` - HTTP caching
- `browser_pool.py` - Browser management

**This means**: Improvements to scraping logic benefit both branches!

---

## Quick Reference

### Switch to Flask Version
```bash
git checkout web
pip install -r requirements_flask.txt
python app.py
```

### Switch to Apify Version
```bash
git checkout main
pip install -r requirements.txt
apify run
```

### Terminal Scraping (Works on Both)
```bash
# Works on web or main branch
python fast_scrape.py https://example.com
```

---

## Development Workflow

### Working on Scraper Logic

1. Make changes on either branch
2. Test locally
3. Commit to current branch
4. Cherry-pick to other branch if needed:

```bash
# On web branch
git commit -m "Improve email extraction"

# Switch to main and apply same change
git checkout main
git cherry-pick <commit-hash>
```

### Working on Flask UI

1. Switch to `web` branch
2. Make UI changes
3. Commit to `web` branch only

```bash
git checkout web
# Make changes to static/templates
git commit -m "Update UI"
```

### Working on Apify Integration

1. Switch to `main` branch
2. Make Apify-specific changes
3. Commit to `main` branch only

```bash
git checkout main
# Make changes to main.py or .actor/
git commit -m "Update Apify config"
```

---

## File Differences

### Files ONLY in `web` branch:
- `app.py` - Flask server
- `app_queue.py` - Flask with queue
- `queue_manager.py` - Redis queue
- `tasks.py` - Celery tasks
- `static/` - UI files
- `templates/` - HTML templates
- `requirements_flask.txt` - Flask dependencies
- `requirements_phase3.txt` - Redis/Celery dependencies
- All `test_*.py` files

### Files ONLY in `main` branch:
- `main.py` - Apify actor
- `.actor/` - Apify configuration
- `Dockerfile` - Apify Docker setup
- `README_APIFY.md` - Apify documentation
- `APIFY_QUICKSTART.md` - Apify quick start
- `test_apify_local.py` - Apify local testing

### Files in BOTH branches:
- All core scraper modules
- `fast_scrape.py` - Terminal scraper
- `requirements.txt` - Core dependencies
- Documentation files

---

## Deployment

### Deploy Flask Version (Local/Server)

```bash
git checkout web

# Option 1: Local development
python app.py

# Option 2: Production server
gunicorn app:app --bind 0.0.0.0:5000 --workers 4
```

### Deploy Apify Version (Cloud)

```bash
git checkout main

# Test locally first
apify run

# Deploy to Apify
apify login
apify push
```

---

## Testing

### Test Flask Version

```bash
git checkout web
python test_complete_system.py
python test_app_backend.py
```

### Test Apify Version

```bash
git checkout main
python test_apify_local.py
```

### Test Core Scraper (Both)

```bash
# Works on either branch
python fast_scrape.py https://example.com
```

---

## Troubleshooting

### "Module not found" error

**Solution**: Install correct requirements for your branch

```bash
# On web branch
pip install -r requirements_flask.txt

# On main branch
pip install -r requirements.txt
```

### Flask won't start on main branch

**Expected**: Flask files are not on `main` branch

**Solution**: Switch to `web` branch

```bash
git checkout web
python app.py
```

### Apify actor won't run on web branch

**Expected**: Apify files are not on `web` branch

**Solution**: Switch to `main` branch

```bash
git checkout main
apify run
```

---

## Summary

| Feature | `web` Branch | `main` Branch |
|---------|-------------|---------------|
| Flask UI | ✅ Yes | ❌ No |
| Terminal Scraper | ✅ Yes | ✅ Yes |
| Apify Actor | ❌ No | ✅ Yes |
| Redis/Celery | ✅ Yes | ❌ No |
| Core Scraper | ✅ Yes | ✅ Yes |
| Best For | Local Dev | Production |

**Both branches work perfectly** - just use the right one for your needs!

---

## Questions?

- Flask issues → Check `web` branch docs
- Apify issues → Check `APIFY_QUICKSTART.md`
- Scraper issues → Check `README.md` (on either branch)

Happy scraping! 🚀
