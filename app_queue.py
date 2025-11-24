"""
Flask Web Scraper API with Job Queue - Phase 3 Implementation
Non-blocking API with Redis + Celery for background processing
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import csv
import io
from datetime import datetime
import logging
import uuid

# Import scraper modules
from scraper import ProxyManager
from async_scraper import scrape_url_async_wrapper
from queue_manager import QueueManager, JobStatus

# Try to import Celery tasks (optional)
try:
    from tasks import scrape_url_task, scrape_batch_task, celery_app
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logging.warning("Celery not available - falling back to synchronous mode")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize components
proxy_manager = ProxyManager()
queue_manager = QueueManager()

# Store results for download
results_cache = {}


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """
    Queue a scraping job (non-blocking)
    Returns job_id immediately for polling
    """
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        if not url.startswith('http'):
            url = f'https://{url}'
        
        # Check cache first
        cached_result = queue_manager.get_cached_url_result(url)
        if cached_result:
            logger.info(f"Cache hit for {url}")
            return jsonify({
                'cached': True,
                'result': cached_result
            })
        
        # Parse options
        options = {
            'fast_mode': data.get('fast_mode', True),
            'enable_validation': data.get('enable_validation', False),
            'block_keywords': data.get('block_keywords', '')
        }
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Store job metadata
        queue_manager.store_job(job_id, url, options)
        
        if CELERY_AVAILABLE:
            # Queue job with Celery
            task = scrape_url_task.apply_async(
                args=[url, options],
                task_id=job_id
            )
            
            logger.info(f"Queued job {job_id} for {url}")
            
            return jsonify({
                'job_id': job_id,
                'status': 'queued',
                'message': 'Job queued successfully',
                'poll_url': f'/api/job/{job_id}'
            }), 202
        else:
            # Fallback to synchronous scraping
            logger.info(f"Scraping {url} synchronously (Celery not available)")
            result = scrape_url_async_wrapper(url, proxy_manager=proxy_manager, fast_mode=True)
            
            result_dict = {
                'url': result.url,
                'success': result.success,
                'emails': list(result.emails),
                'phones': list(result.phones),
                'social_links': result.social_links,
                'company_name': result.company_name,
                'address': result.address,
                'fetch_time': result.fetch_time,
                'confidence_score': result.confidence_score
            }
            
            # Cache result
            queue_manager.cache_url_result(url, result_dict)
            
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'result': result_dict
            })
    
    except Exception as e:
        logger.error(f"Scrape error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Poll job status and get results when ready
    """
    try:
        if CELERY_AVAILABLE:
            # Get task status from Celery
            task = celery_app.AsyncResult(job_id)
            
            if task.state == 'PENDING':
                return jsonify({
                    'job_id': job_id,
                    'status': 'pending',
                    'message': 'Job is waiting in queue'
                })
            
            elif task.state == 'PROCESSING':
                meta = task.info or {}
                return jsonify({
                    'job_id': job_id,
                    'status': 'processing',
                    'message': meta.get('status', 'Processing'),
                    'progress': meta.get('progress', 0)
                })
            
            elif task.state == 'SUCCESS':
                result = task.result
                
                # Cache result by URL
                if result and 'url' in result:
                    queue_manager.cache_url_result(result['url'], result)
                
                return jsonify({
                    'job_id': job_id,
                    'status': 'completed',
                    'result': result
                })
            
            elif task.state == 'FAILURE':
                return jsonify({
                    'job_id': job_id,
                    'status': 'failed',
                    'error': str(task.info)
                }), 500
            
            else:
                return jsonify({
                    'job_id': job_id,
                    'status': task.state.lower(),
                    'message': f'Task state: {task.state}'
                })
        
        else:
            # Fallback: check queue manager
            job_data = queue_manager.get_job(job_id)
            if not job_data:
                return jsonify({'error': 'Job not found'}), 404
            
            result = queue_manager.get_result(job_id)
            if result:
                return jsonify({
                    'job_id': job_id,
                    'status': 'completed',
                    'result': result
                })
            
            return jsonify({
                'job_id': job_id,
                'status': job_data.get('status', 'unknown'),
                'message': 'Job status unknown'
            })
    
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch', methods=['POST'])
def batch_scrape():
    """
    Queue batch scraping job (non-blocking)
    """
    try:
        data = request.json
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'URLs required'}), 400
        
        # Parse options
        options = {
            'fast_mode': data.get('fast_mode', True),
            'enable_validation': data.get('enable_validation', False)
        }
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Store job metadata
        queue_manager.store_job(job_id, f"batch:{len(urls)}_urls", options)
        
        if CELERY_AVAILABLE:
            # Queue batch job with Celery
            task = scrape_batch_task.apply_async(
                args=[urls, options],
                task_id=job_id
            )
            
            logger.info(f"Queued batch job {job_id} for {len(urls)} URLs")
            
            return jsonify({
                'job_id': job_id,
                'status': 'queued',
                'total_urls': len(urls),
                'message': 'Batch job queued successfully',
                'poll_url': f'/api/job/{job_id}'
            }), 202
        
        else:
            # Fallback to synchronous batch scraping
            logger.info(f"Batch scraping {len(urls)} URLs synchronously")
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            results = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(scrape_url_async_wrapper, url, proxy_manager, True): url for url in urls}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append({
                            'url': result.url,
                            'success': result.success,
                            'emails': list(result.emails),
                            'phones': list(result.phones)
                        })
                    except Exception as e:
                        url = futures[future]
                        results.append({
                            'url': url,
                            'success': False,
                            'error': str(e)
                        })
            
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'results': results,
                'total': len(results)
            })
    
    except Exception as e:
        logger.error(f"Batch scrape error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/queue/stats', methods=['GET'])
def queue_stats():
    """Get queue statistics"""
    try:
        stats = queue_manager.get_queue_stats()
        
        if CELERY_AVAILABLE:
            # Add Celery worker stats
            inspect = celery_app.control.inspect()
            active = inspect.active()
            stats['workers'] = len(active) if active else 0
            stats['active_tasks'] = sum(len(tasks) for tasks in active.values()) if active else 0
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting queue stats: {str(e)}")
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
        fieldnames = ['url', 'success', 'emails', 'phones', 'company_name', 'address', 'confidence_score']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'url': result.get('url'),
                'success': result.get('success'),
                'emails': '; '.join(result.get('emails', [])),
                'phones': '; '.join(result.get('phones', [])),
                'company_name': result.get('company_name', ''),
                'address': result.get('address', ''),
                'confidence_score': result.get('confidence_score', 0)
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


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    # Check if Redis is available
    if queue_manager.redis_client:
        logger.info("Redis connected - queue system ready")
    else:
        logger.warning("Redis not available - running in fallback mode")
    
    if CELERY_AVAILABLE:
        logger.info("Celery available - background processing enabled")
    else:
        logger.warning("Celery not available - running in synchronous mode")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
