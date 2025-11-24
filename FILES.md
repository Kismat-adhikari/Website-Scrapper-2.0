# Project Files

Complete list of all project files and their purposes.

## Core Files

### scraper.py
**Purpose**: Main scraper implementation

**Size**: ~1000 lines

**Contains**:
- `FetchMode` enum - Fetch mode types
- `ScrapeMode` enum - Scrape mode types
- `PreCheckResult` dataclass - Pre-check results
- `ScraperResult` dataclass - Scraper results
- `PreCheckSystem` class - Pre-check validation
- `FetchModeSelector` class - Fetch mode selection
- `PageDiscovery` class - Page discovery
- `AntiBlockingHeaders` class - Anti-blocking headers
- `ProxyManager` class - Proxy management
- `ContactExtractor` class - Information extraction
- `WebScraper` class - Main scraping engine
- `load_urls()` function - URL loading
- `main()` function - CLI entry point

**Usage**: `python scraper.py <urls> [options]`

### requirements.txt
**Purpose**: Python dependencies

**Contents**:
```
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
playwright==1.40.0
```

**Usage**: `pip install -r requirements.txt`

## Configuration Files

### proxies.txt
**Purpose**: Proxy configuration

**Format**:
```
# Basic proxy
192.168.1.1:8080

# Authenticated proxy
10.0.0.1:3128:username:password
```

**Usage**: `python scraper.py urls.txt --proxy-file proxies.txt`

### sample_urls.txt
**Purpose**: Sample URLs for testing

**Contents**:
```
https://example.com
https://github.com
https://stackoverflow.com
```

**Usage**: `python scraper.py sample_urls.txt`

## Documentation Files

### README.md
**Purpose**: Main documentation

**Sections**:
- Features
- Installation
- Usage
- Proxy configuration
- Output columns
- Architecture
- Performance tips
- Fetch mode strategy

**Read**: First comprehensive overview

### QUICK_START.md
**Purpose**: Quick start guide

**Sections**:
- Installation
- Basic usage
- Common use cases
- Output format
- Configuration
- Logging
- Examples
- Troubleshooting
- Performance benchmarks
- Tips & tricks

**Read**: For quick setup and common tasks

### FETCH_MODES.md
**Purpose**: Fetch modes documentation

**Sections**:
- Overview
- Fast HTML mode
- JS Rendering mode
- Hard Mode
- Mode selection algorithm
- Configuration
- Performance tuning
- Troubleshooting
- Best practices
- Examples

**Read**: For fetch mode details and optimization

### EXTRACTION_GUIDE.md
**Purpose**: Contact information extraction and confidence scoring

**Sections**:
- Email extraction and filtering
- Phone number extraction and normalization
- Leadership title detection
- Social media link extraction
- Confidence score calculation
- Output format
- Extraction tips
- Troubleshooting
- Advanced usage

**Read**: For extraction details and confidence scoring

### RETRY_RECOVERY.md
**Purpose**: Retry logic, failure detection, and recovery strategies

**Sections**:
- Failure reasons (timeout, blocked, SSL, bot detection, etc.)
- Retry strategy by mode
- Exponential backoff
- Mode escalation
- Failure logging
- Problematic site tracking
- Retry configuration
- Failure analysis
- Best practices
- Troubleshooting

**Read**: For retry and recovery details

### MULTITHREADING.md
**Purpose**: Multi-threading, thread pool, and proxy rotation

**Sections**:
- Thread pool architecture
- Thread configuration
- Thread safety
- Proxy rotation (sequential and random)
- Performance tuning
- Retry logic in threads
- Monitoring
- Common issues
- Best practices
- Performance benchmarks

**Read**: For multi-threading and concurrency details

### CSV_OUTPUT.md
**Purpose**: CSV output format, columns, and analysis

**Sections**:
- CSV columns and data types
- Column details and values
- Example CSV output
- Data format details
- UTF-8 encoding
- Reading CSV files
- Analyzing results
- CSV customization
- Troubleshooting
- Best practices

**Read**: For CSV output details and analysis

### PAGE_DISCOVERY.md
**Purpose**: Page discovery documentation

**Sections**:
- Overview
- Discovery process
- Contact page keywords
- Team/Leadership keywords
- Exclusion patterns
- URL normalization
- Deduplication
- Configuration
- Discovery limits
- Output analysis
- Performance impact
- Examples
- Troubleshooting
- Best practices

**Read**: For page discovery details and customization

### IMPLEMENTATION_SUMMARY.md
**Purpose**: Technical implementation details

**Sections**:
- Project structure
- Core components
- Data flow
- Configuration options
- Output format
- Performance characteristics
- Error handling
- Logging
- Dependencies
- Usage examples
- Best practices
- Troubleshooting
- Future enhancements

**Read**: For technical deep dive

### DOCUMENTATION.md
**Purpose**: Documentation index

**Sections**:
- Quick navigation
- File descriptions
- Reading paths
- Common questions
- Feature matrix
- Troubleshooting guide
- Configuration reference
- Performance reference
- API reference
- Support resources

**Read**: To navigate all documentation

### FILES.md
**Purpose**: This file - project files overview

**Sections**:
- Core files
- Configuration files
- Documentation files
- Example files
- Generated files
- File organization

**Read**: To understand project structure

## Example Files

### example_usage.py
**Purpose**: Usage examples

**Contains** (10 examples):
1. `example_basic()` - Basic scraping with pre-check
2. `example_precheck_only()` - Pre-check validation only
3. `example_with_proxies()` - Using proxies
4. `example_analyze_precheck()` - Analyzing pre-check results
5. `example_fetch_modes()` - Fetch mode selection
6. `example_hard_mode()` - Hard mode with custom delay
7. `example_fetch_mode_analysis()` - Fetch mode distribution
8. `example_page_discovery()` - Page discovery
9. `example_page_discovery_dedup()` - Page discovery with deduplication
10. `example_scraping_with_discovery()` - Scraping with page discovery

**Usage**: `python example_usage.py` (then uncomment examples)

## Generated Files

### scraper.log
**Purpose**: Execution logs

**Format**: `timestamp - level - message`

**Levels**: INFO, DEBUG, WARNING, ERROR

**Location**: Generated in project root

**Usage**: `tail -f scraper.log` (monitor in real-time)

### results.csv
**Purpose**: Scraping results

**Format**: CSV with headers

**Columns**: 15 columns (see README.md)

**Location**: Generated in project root (or custom with `--output`)

**Usage**: Open in Excel, Google Sheets, or text editor

## File Organization

```
project/
├── Core Implementation
│   ├── scraper.py              (main implementation)
│   ├── requirements.txt         (dependencies)
│   └── example_usage.py         (examples)
│
├── Configuration
│   ├── proxies.txt              (proxy config)
│   └── sample_urls.txt          (sample URLs)
│
├── Documentation
│   ├── README.md                (main docs)
│   ├── QUICK_START.md           (quick start)
│   ├── FETCH_MODES.md           (fetch modes)
│   ├── PAGE_DISCOVERY.md        (page discovery)
│   ├── IMPLEMENTATION_SUMMARY.md (technical)
│   ├── DOCUMENTATION.md         (index)
│   └── FILES.md                 (this file)
│
└── Generated (at runtime)
    ├── scraper.log              (logs)
    └── results.csv              (results)
```

## File Dependencies

```
scraper.py
├── Imports: requests, beautifulsoup4, selenium, playwright
├── Uses: proxies.txt (optional)
└── Generates: scraper.log, results.csv

example_usage.py
├── Imports: scraper.py
└── Uses: proxies.txt (optional)

README.md
├── References: FETCH_MODES.md, PAGE_DISCOVERY.md
└── Describes: scraper.py

QUICK_START.md
├── References: README.md, FETCH_MODES.md, PAGE_DISCOVERY.md
└── Describes: scraper.py usage

FETCH_MODES.md
├── References: README.md
└── Describes: scraper.py fetch modes

PAGE_DISCOVERY.md
├── References: README.md
└── Describes: scraper.py page discovery

IMPLEMENTATION_SUMMARY.md
├── References: All documentation
└── Describes: scraper.py implementation

DOCUMENTATION.md
├── References: All documentation files
└── Provides: Navigation and index

FILES.md (this file)
├── References: All files
└── Provides: File organization
```

## File Sizes (Approximate)

| File | Size | Type |
|------|------|------|
| scraper.py | 1200 lines | Code |
| example_usage.py | 250 lines | Code |
| requirements.txt | 4 lines | Config |
| proxies.txt | 3 lines | Config |
| sample_urls.txt | 3 lines | Config |
| README.md | 350 lines | Docs |
| QUICK_START.md | 400 lines | Docs |
| FETCH_MODES.md | 500 lines | Docs |
| PAGE_DISCOVERY.md | 600 lines | Docs |
| EXTRACTION_GUIDE.md | 600 lines | Docs |
| IMPLEMENTATION_SUMMARY.md | 700 lines | Docs |
| DOCUMENTATION.md | 450 lines | Docs |
| FILES.md | 350 lines | Docs |

## File Modification Guide

### To Add Custom Keywords
Edit `scraper.py`:
```python
class PageDiscovery:
    CONTACT_KEYWORDS = [
        'contact', 'support',
        'your-keyword'  # Add here
    ]
```

### To Add Exclusion Patterns
Edit `scraper.py`:
```python
class PageDiscovery:
    EXCLUDE_PATTERNS = [
        r'\.pdf$',
        r'/your-pattern'  # Add here
    ]
```

### To Add User-Agents
Edit `scraper.py`:
```python
class AntiBlockingHeaders:
    USER_AGENTS = [
        'Mozilla/5.0...',
        'Your-User-Agent'  # Add here
    ]
```

### To Change Default Values
Edit `scraper.py` or use command line arguments:
```bash
python scraper.py urls.txt --timeout 20 --threads 10
```

## Backup Recommendations

### Important Files to Backup
- `scraper.py` - Main implementation
- `proxies.txt` - Proxy configuration
- `results.csv` - Results (after scraping)

### Optional Backups
- `scraper.log` - Logs (for debugging)
- Documentation files (for reference)

### Backup Command
```bash
tar -czf backup.tar.gz scraper.py proxies.txt results.csv
```

## Cleanup

### Remove Generated Files
```bash
rm scraper.log results.csv
```

### Remove All Generated Files
```bash
rm scraper.log results*.csv
```

### Keep Only Source
```bash
rm scraper.log results*.csv *.pyc __pycache__
```

## Version Control

### .gitignore Recommendations
```
# Generated files
scraper.log
results.csv
results_*.csv

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Sensitive
proxies.txt
```

### Git Commands
```bash
# Initialize repository
git init

# Add files
git add scraper.py requirements.txt README.md

# Commit
git commit -m "Initial commit"

# Ignore generated files
echo "scraper.log" >> .gitignore
echo "results.csv" >> .gitignore
```

## Distribution

### Files to Include
- `scraper.py`
- `requirements.txt`
- `README.md`
- `QUICK_START.md`
- `FETCH_MODES.md`
- `PAGE_DISCOVERY.md`
- `IMPLEMENTATION_SUMMARY.md`
- `DOCUMENTATION.md`
- `example_usage.py`
- `proxies.txt` (template)
- `sample_urls.txt`

### Files to Exclude
- `scraper.log` (generated)
- `results.csv` (generated)
- `__pycache__/` (generated)
- `.git/` (version control)

### Distribution Package
```bash
tar -czf web-scraper.tar.gz \
  scraper.py \
  requirements.txt \
  README.md \
  QUICK_START.md \
  FETCH_MODES.md \
  PAGE_DISCOVERY.md \
  IMPLEMENTATION_SUMMARY.md \
  DOCUMENTATION.md \
  FILES.md \
  example_usage.py \
  proxies.txt \
  sample_urls.txt
```

## File Checklist

### Before Running
- [ ] `scraper.py` exists
- [ ] `requirements.txt` exists
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] URLs prepared (file or command line)
- [ ] Proxies configured (if needed)

### After Running
- [ ] `scraper.log` generated
- [ ] `results.csv` generated
- [ ] Results verified
- [ ] Logs reviewed for errors

### Before Distribution
- [ ] All documentation files present
- [ ] `scraper.py` tested
- [ ] `example_usage.py` works
- [ ] `README.md` up to date
- [ ] No sensitive data in files

## Related Files

### External Dependencies
- Python 3.7+ (system)
- Chrome/Chromium (system)
- ChromeDriver (for Selenium)

### Optional Files
- `.gitignore` (version control)
- `setup.py` (distribution)
- `LICENSE` (licensing)
- `CHANGELOG.md` (version history)

## Support

For file-related questions:
1. Check this file (FILES.md)
2. Check DOCUMENTATION.md for navigation
3. Check README.md for overview
4. Check QUICK_START.md for usage

---

**Last Updated**: 2024
**Version**: 1.0.0
