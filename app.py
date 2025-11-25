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
from async_scraper import scrape_url_async_wrapper, scrape_urls_batch_wrapper
from aggressive_scraper import create_aggressive_scraper
from email_validator import create_validator
from role_detector import create_role_detector
from advanced_scraper_features import CompanyInfoExtractor, AddressExtractor
from context_extractor import ContextExtractor
from schema_extractor import SchemaExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Disable caching for API responses
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Initialize components
proxy_manager = ProxyManager()
scraper = WebScraper(proxy_manager, enable_precheck=True)
email_validator = create_validator(enable_smtp=True, enable_role_detection=True, smtp_max_workers=10)
role_detector = create_role_detector()
company_extractor = CompanyInfoExtractor()
address_extractor = AddressExtractor()
context_extractor = ContextExtractor()
schema_extractor = SchemaExtractor()

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
        
        # Create logs list to send back
        logs = []
        
        logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': f'🔍 Starting scrape for {url}', 'type': 'info'})
        logger.info(f"Scraping {url}")
        
        # Try async scraper first (super fast - main page only)
        logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': '⚡ Trying fast HTTP scraper...', 'type': 'info'})
        result = scrape_url_async_wrapper(url, proxy_manager=proxy_manager, fast_mode=True)
        
        # Only use aggressive mode if completely failed (not just no data)
        # This makes it much faster - most sites work with async
        if result.status == 'failed':
            logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': '❌ Fast scraper failed', 'type': 'warning'})
            logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': '🚀 Trying aggressive mode...', 'type': 'info'})
            logger.info(f"Async scraper failed for {url}, trying aggressive mode")
            aggressive = create_aggressive_scraper(scraper)
            result = aggressive.scrape_aggressive(url)
        else:
            logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': '✓ Fast scraper succeeded', 'type': 'success'})
        
        # Check if scraping failed
        if not result or result.status == 'failed':
            error_reason = getattr(result, 'reason', 'Unknown error') if result else 'Scraping failed'
            logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': f'❌ Scraping failed: {error_reason}', 'type': 'error'})
            logger.error(f"Scraping failed for {url}: {error_reason}")
            return jsonify({
                'url': url,
                'status': 'failed',
                'reason': error_reason,
                'emails': [],
                'phones': [],
                'confidence_score': 0,
                'company_name': None,
                'addresses': [],
                'logs': logs
            })
        
        # Quick company name extraction only (for speed)
        company_name = None
        company_description = None  # Skip for speed
        addresses = []  # Skip for speed
        
        if hasattr(result, 'html') and result.html:
            try:
                # Only extract company name (fast, ~0.1s)
                company_name = company_extractor.extract_company_name(result.html)
            except Exception as e:
                logger.warning(f"Error extracting company name for {url}: {str(e)}")
        
        # Get emails and phones (handle both set and list)
        emails = list(result.emails) if hasattr(result, 'emails') else []
        phones = list(result.phones) if hasattr(result, 'phones') else []
        
        logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': f'📧 Found {len(emails)} emails, {len(phones)} phones', 'type': 'success'})
        
        # Apply keyword blocking
        if block_keywords and emails:
            keywords = [kw.strip().lower() for kw in block_keywords.split(',') if kw.strip()]
            original_count = len(emails)
            emails = [e for e in emails if not any(kw in e.lower() for kw in keywords)]
            if original_count != len(emails):
                logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': f'🚫 Filtered {original_count - len(emails)} emails by keywords', 'type': 'info'})
        if block_keywords and phones:
            keywords = [kw.strip().lower() for kw in block_keywords.split(',') if kw.strip()]
            original_count = len(phones)
            phones = [p for p in phones if not any(kw in p.lower() for kw in keywords)]
            if original_count != len(phones):
                logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': f'🚫 Filtered {original_count - len(phones)} phones by keywords', 'type': 'info'})
        
        # Skip email validation for speed - emails already have syntax/MX checks
        email_categories = {}
        
        # Convert addresses to strings
        addresses_str = [str(addr) for addr in addresses] if addresses else []
        
        logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'message': '✅ Scraping complete!', 'type': 'success'})
        
        # Build response with safe attribute access
        response = {
            'url': result.url if hasattr(result, 'url') else url,
            'status': result.status if hasattr(result, 'status') else 'success',
            'emails': emails,
            'phones': phones,
            'email_categories': email_categories,
            'pages_scanned': getattr(result, 'pages_scanned', 1),
            'leadership_count': getattr(result, 'leadership_count', 0),
            'confidence_score': round(getattr(result, 'confidence_score', 0.0), 2),
            'fetch_mode': getattr(result, 'fetch_mode', 'unknown'),
            'load_time': round(getattr(result, 'load_time', 0.0), 2),
            'ssl_valid': getattr(result, 'ssl_valid', True),
            'bot_protection': getattr(result, 'bot_protection', False),
            'scrape_mode': getattr(result, 'scrape_mode', 'fast'),
            'retry_count': getattr(result, 'retry_count', 0),
            'social_links': getattr(result, 'social_links', {}),
            'reason': getattr(result, 'reason', ''),
            'company_name': company_name,
            'company_description': company_description,
            'addresses': addresses_str,
            'data_quality_score': 0,
            'logs': logs
        }
        
        # Cache for download
        results_cache[url] = response
        
        return jsonify(response)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Scrape error: {str(e)}\n{error_trace}")
        return jsonify({'error': str(e), 'trace': error_trace}), 500


def scrape_single_url(url):
    """Helper function to scrape a single URL (for parallel processing) - PHASE 2: Using async"""
    if not url.startswith('http'):
        url = f'https://{url}'
    
    try:
        # PHASE 2: Use async scraper for better performance
        result = scrape_url_async_wrapper(url, proxy_manager=proxy_manager, fast_mode=True)
        
        # Check if scraping was successful
        if not result or result.status == 'failed':
            logger.warning(f"Scraping failed for {url}: {getattr(result, 'reason', 'Unknown error')}")
            return {
                'url': url,
                'status': 'failed',
                'emails': [],
                'phones': [],
                'confidence_score': 0,
                'company_name': None,
                'company_description': None,
                'addresses': [],
                'reason': getattr(result, 'reason', 'Scraping failed')
            }
        
        # Quick company/address extraction from HTML
        company_name = None
        company_description = None
        addresses = []
        
        if hasattr(result, 'html') and result.html:
            try:
                # Extract company info
                company_name = company_extractor.extract_company_name(result.html)
                company_description = company_extractor.extract_company_description(result.html)
                
                # Try multiple address extraction methods
                schema_data = schema_extractor.extract_all(result.html)
                if schema_data and 'address' in schema_data:
                    addr_data = schema_data['address']
                    if isinstance(addr_data, dict):
                        addr_str = f"{addr_data.get('streetAddress', '')}, {addr_data.get('addressLocality', '')}, {addr_data.get('addressRegion', '')} {addr_data.get('postalCode', '')}".strip(', ')
                        if addr_str:
                            addresses.append(addr_str)
                
                context_addresses = context_extractor.extract_addresses_with_context(result.html)
                addresses.extend(context_addresses)
                
                pattern_addresses = address_extractor.extract_addresses(result.html)
                addresses.extend([str(addr) for addr in pattern_addresses])
                
                addresses = list(set(addresses))
                
            except Exception as e:
                logger.warning(f"Error extracting company/address for {url}: {str(e)}")
        
        # Convert addresses to strings
        addresses_str = [str(addr) for addr in addresses] if addresses else []
        
        return {
            'url': result.url,
            'status': result.status,
            'emails': list(result.emails) if hasattr(result, 'emails') else [],
            'phones': list(result.phones) if hasattr(result, 'phones') else [],
            'confidence_score': round(result.confidence_score, 2) if hasattr(result, 'confidence_score') else 0,
            'company_name': company_name,
            'company_description': company_description,
            'addresses': addresses_str,
            'social_links': result.social_links if hasattr(result, 'social_links') else {},
            'fetch_time': round(result.fetch_time, 2) if hasattr(result, 'fetch_time') else 0
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)
        return {
            'url': url,
            'status': 'failed',
            'emails': [],
            'phones': [],
            'confidence_score': 0,
            'company_name': None,
            'company_description': None,
            'addresses': [],
            'reason': str(e)
        }


@app.route('/api/batch', methods=['POST'])
def batch_scrape():
    """Scrape multiple URLs in parallel"""
    try:
        data = request.json
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'URLs required'}), 400
        
        # Clean and validate URLs
        cleaned_urls = []
        for url in urls:
            url = url.strip()
            if url:
                if not url.startswith('http'):
                    url = f'https://{url}'
                cleaned_urls.append(url)
        
        if not cleaned_urls:
            return jsonify({'error': 'No valid URLs provided'}), 400
        
        logger.info(f"Batch scraping {len(cleaned_urls)} URLs using async batch scraper")
        
        try:
            # Use async batch scraper for better performance
            results_objs = scrape_urls_batch_wrapper(cleaned_urls, proxy_manager=proxy_manager, fast_mode=True)
            
            # Convert results to dict format
            results = []
            for result in results_objs:
                # Extract company/address info if available
                company_name = None
                company_description = None
                addresses = []
                
                if hasattr(result, 'html') and result.html:
                    try:
                        # Extract company info
                        company_name = company_extractor.extract_company_name(result.html)
                        company_description = company_extractor.extract_company_description(result.html)
                        
                        # Try multiple address extraction methods
                        schema_data = schema_extractor.extract_all(result.html)
                        if schema_data and 'address' in schema_data:
                            addr_data = schema_data['address']
                            if isinstance(addr_data, dict):
                                addr_str = f"{addr_data.get('streetAddress', '')}, {addr_data.get('addressLocality', '')}, {addr_data.get('addressRegion', '')} {addr_data.get('postalCode', '')}".strip(', ')
                                if addr_str:
                                    addresses.append(addr_str)
                        
                        context_addresses = context_extractor.extract_addresses_with_context(result.html)
                        addresses.extend(context_addresses)
                        
                        pattern_addresses = address_extractor.extract_addresses(result.html)
                        addresses.extend([str(addr) for addr in pattern_addresses])
                        
                        addresses = list(set(addresses))
                        
                    except Exception as e:
                        logger.warning(f"Error extracting company/address for {result.url}: {str(e)}")
                
                # Convert addresses to strings
                addresses_str = [str(addr) for addr in addresses] if addresses else []
                
                results.append({
                    'url': result.url,
                    'status': result.status,
                    'emails': list(result.emails) if hasattr(result, 'emails') else [],
                    'phones': list(result.phones) if hasattr(result, 'phones') else [],
                    'confidence_score': round(result.confidence_score, 2) if hasattr(result, 'confidence_score') else 0,
                    'company_name': company_name,
                    'company_description': company_description,
                    'addresses': addresses_str,
                    'social_links': result.social_links if hasattr(result, 'social_links') else {},
                    'fetch_time': round(result.fetch_time, 2) if hasattr(result, 'fetch_time') else 0
                })
            
            logger.info(f"Batch scraping completed: {len(results)} URLs processed")
            return jsonify({'results': results, 'total': len(results)})
            
        except Exception as e:
            logger.error(f"Async batch scraper failed: {str(e)}, falling back to ThreadPoolExecutor")
            
            # Fallback to ThreadPoolExecutor if async batch fails
            from concurrent.futures import ThreadPoolExecutor, as_completed
            results = []
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(scrape_single_url, url): url for url in cleaned_urls}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        url = futures[future]
                        logger.error(f"Error processing {url}: {str(e)}")
                        results.append({
                            'url': url,
                            'status': 'failed',
                            'emails': [],
                            'phones': [],
                            'confidence_score': 0,
                            'company_name': None,
                            'company_description': None,
                            'addresses': [],
                            'reason': str(e)
                        })
            
            return jsonify({'results': results, 'total': len(results)})
    
    except Exception as e:
        logger.error(f"Batch scrape error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export_results():
    """Export results as CSV"""
    try:
        data = request.json
        results = data.get('results', [])
        
        if not results:
            return jsonify({'error': 'No results to export'}), 400
        
        # Create CSV with all fields
        output = io.StringIO()
        fieldnames = [
            'url', 'status', 'emails', 'phones', 'confidence_score',
            'pages_scanned', 'leadership_count', 'fetch_mode', 'scrape_mode',
            'retry_count', 'load_time', 'ssl_valid', 'bot_protection', 'reason'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'url': result.get('url'),
                'status': result.get('status'),
                'emails': '; '.join(result.get('emails', [])),
                'phones': '; '.join(result.get('phones', [])),
                'confidence_score': result.get('confidence_score'),
                'pages_scanned': result.get('pages_scanned'),
                'leadership_count': result.get('leadership_count'),
                'fetch_mode': result.get('fetch_mode'),
                'scrape_mode': result.get('scrape_mode'),
                'retry_count': result.get('retry_count'),
                'load_time': result.get('load_time'),
                'ssl_valid': result.get('ssl_valid'),
                'bot_protection': result.get('bot_protection'),
                'reason': result.get('reason')
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
