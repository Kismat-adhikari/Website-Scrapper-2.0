# Web Scraper Flask API

Fast, modern web interface for extracting contact information from websites.

## Features

✅ **Single URL Scraping** - Extract emails, phones, and contact info
✅ **Batch Processing** - Scrape multiple URLs at once
✅ **Email Validation** - SMTP verification with confidence scoring
✅ **Role Detection** - Identify personal vs generic emails
✅ **Aggressive Mode** - Try multiple strategies for difficult sites
✅ **Keyword Blocking** - Filter results by keywords
✅ **CSV Export** - Download results as CSV

## Installation

1. Install dependencies:
```bash
pip install -r requirements_flask.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

## Running

Start the Flask server:
```bash
python app.py
```

Then open your browser to: `http://localhost:5000`

## API Endpoints

### POST /api/scrape
Scrape a single URL

**Request:**
```json
{
    "url": "https://example.com",
    "aggressive": false,
    "block_keywords": "noreply, @outlook"
}
```

**Response:**
```json
{
    "url": "https://example.com",
    "status": "success",
    "emails": ["contact@example.com"],
    "phones": ["+1-555-0123"],
    "email_categories": {
        "personal": ["contact@example.com"],
        "role_based": [],
        "generic": [],
        "unknown": []
    },
    "pages_scanned": 2,
    "leadership_count": 3,
    "confidence_score": 0.85,
    "fetch_mode": "fast_html",
    "load_time": 2.5
}
```

### POST /api/batch
Scrape multiple URLs

**Request:**
```json
{
    "urls": ["https://example1.com", "https://example2.com"],
    "aggressive": false
}
```

### POST /api/validate-email
Validate a single email

**Request:**
```json
{
    "email": "john@example.com"
}
```

**Response:**
```json
{
    "email": "john@example.com",
    "is_valid": true,
    "confidence": 0.92,
    "reason": "valid",
    "email_type": "personal",
    "is_personal": true,
    "is_generic": false
}
```

### POST /api/export
Export results as CSV

**Request:**
```json
{
    "results": [...]
}
```

### GET /api/stats
Get scraper statistics

## Usage

### Web Interface

1. **Single URL Tab**
   - Enter website URL
   - Optionally add keywords to block
   - Enable aggressive mode for difficult sites
   - Click "Scrape Website"

2. **Batch URLs Tab**
   - Enter multiple URLs (one per line)
   - Enable aggressive mode if needed
   - Click "Scrape All"

3. **Validate Email Tab**
   - Enter email address
   - Click "Validate Email"
   - See validation details and email type

### Command Line (Python)

```python
import requests

# Scrape single URL
response = requests.post('http://localhost:5000/api/scrape', json={
    'url': 'https://example.com',
    'aggressive': False,
    'block_keywords': ''
})
print(response.json())

# Validate email
response = requests.post('http://localhost:5000/api/validate-email', json={
    'email': 'john@example.com'
})
print(response.json())
```

## Scraping Modes

### Standard Mode
- Fast HTML fetch (requests)
- JS rendering (Playwright)
- Hard mode (anti-blocking)

### Aggressive Mode
- Tries all strategies automatically
- Handles protected sites
- Handles slow-loading sites
- Learns what works per domain

## Performance

- **Single URL**: 2-10 seconds (depends on site complexity)
- **Batch (10 URLs)**: 20-60 seconds
- **Email Validation**: 0.5-2 seconds per email
- **Parallel Processing**: 5 workers by default

## Configuration

Edit `app.py` to customize:
- Port: Change `port=5000`
- Workers: Change `max_workers=5`
- Timeout: Change `timeout=10`
- Debug: Change `debug=True`

## Troubleshooting

**"Playwright not found"**
```bash
playwright install
```

**"Port 5000 already in use"**
```bash
python app.py --port 5001
```

**"SMTP verification slow"**
- Disable SMTP: Set `enable_smtp=False` in app.py
- Or increase timeout: Set `smtp_timeout=10`

## License

MIT
