"""
Flask Web Scraper API
Fast, modern interface for the web scraper with real-time results.
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import csv
import io
from datetime import datetime
import threading
import logging

# Import scraper modules
from scraper import WebScraper, ProxyManager
from aggressive_scraper import create_aggressive_scraper
from email_validator import create_validator
from role_detector import create_role_detector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize components
proxy_manager = ProxyManager()
scraper = WebScraper(proxy_manager, enable_precheck=True)
email_validator = create_validator(enable_smtp=True, enable_role_detection=True)
role_detector = create_role_detector()

# Store results for download
results_cache = {}


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Scrape a single URL"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        block_keywords = data.get('block_keywords', '')
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        if not url.startswith('http'):
            url = f'https://{url}'
        
        logger.info(f"Scraping {url}")
        
        # Scrape with auto-aggressive enabled (will escalate if needed)
        result = scraper.scrape_url(url, auto_aggressive=True)
        
        # Apply keyword blocking
        if block_keywords:
            keywords = [kw.strip().lower() for kw in block_keywords.split(',') if kw.strip()]
            result.emails = [e for e in result.emails if not any(kw in e.lower() for kw in keywords)]
            result.phones = [p for p in result.phones if not any(kw in p.lower() for kw in keywords)]
        
        # Validate emails automatically during scraping
        if result.emails:
            logger.info(f"Validating {len(result.emails)} emails from {url}")
            validated, summary = email_validator.validate_emails(result.emails, url, use_batch_smtp=True)
            result.emails = [r.email for r in validated if r.is_valid]
            logger.info(f"After validation: {len(result.emails)} valid emails")
        
        # Categorize emails
        email_categories = role_detector.categorize(result.emails) if result.emails else {}
        
        response = {
            'url': result.url,
            'status': result.status,
            'emails': result.emails,
            'phones': result.phones,
            'email_categories': email_categories,
            'pages_scanned': result.pages_scanned,
            'leadership_count': result.leadership_count,
            'confidence_score': round(result.confidence_score, 2),
            'fetch_mode': result.fetch_mode,
            'load_time': round(result.load_time, 2)
        }
        
        # Cache for download
        results_cache[url] = response
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Scrape error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch', methods=['POST'])
def batch_scrape():
    """Scrape multiple URLs"""
    try:
        data = request.json
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'URLs required'}), 400
        
        logger.info(f"Batch scraping {len(urls)} URLs")
        
        results = []
        for url in urls:
            if not url.startswith('http'):
                url = f'https://{url}'
            
            # Auto-aggressive: will escalate if normal modes fail
            result = scraper.scrape_url(url, auto_aggressive=True)
            
            # Validate emails automatically
            if result.emails:
                validated, summary = email_validator.validate_emails(result.emails, url, use_batch_smtp=True)
                result.emails = [r.email for r in validated if r.is_valid]
            
            results.append({
                'url': result.url,
                'status': result.status,
                'emails': result.emails,
                'phones': result.phones,
                'confidence_score': round(result.confidence_score, 2)
            })
        
        return jsonify({'results': results, 'total': len(results)})
    
    except Exception as e:
        logger.error(f"Batch scrape error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export_results():
    """Export results as CSV"""
    try:
        data = request.json
        results = data.get('results', [])
        
        if not results:
            return jsonify({'error': 'No results to export'}), 400
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['url', 'status', 'emails', 'phones', 'confidence_score'])
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'url': result.get('url'),
                'status': result.get('status'),
                'emails': '; '.join(result.get('emails', [])),
                'phones': '; '.join(result.get('phones', [])),
                'confidence_score': result.get('confidence_score')
            })
        
        # Return as file
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"scraper_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get scraper statistics"""
    try:
        stats = {
            'smtp': email_validator.get_stats(),
            'cached_results': len(results_cache),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
