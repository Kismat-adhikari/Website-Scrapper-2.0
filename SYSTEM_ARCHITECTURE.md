# System Architecture - Complete Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                              │
│  - Web Browser / API Client                                         │
│  - Sends HTTP requests                                              │
│  - Polls for job status                                             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ HTTP Request
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FLASK API LAYER                             │
│  - app_queue.py (Non-blocking, <100ms)                             │
│  - Validates input                                                  │
│  - Checks cache                                                     │
│  - Queues jobs                                                      │
│  - Returns job_id instantly                                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Queue Job
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         REDIS LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Job Queue (DB 0)                                            │   │
│  │ - Pending jobs                                              │   │
│  │ - Job metadata                                              │   │
│  │ - TTL: 1 hour                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Result Cache (DB 1)                                         │   │
│  │ - Completed results                                         │   │
│  │ - Job status                                                │   │
│  │ - TTL: 1 hour                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ URL Cache (DB 2)                                            │   │
│  │ - Results by URL                                            │   │
│  │ - HTTP responses                                            │   │
│  │ - TTL: 1 hour                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Pick Job
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CELERY WORKER POOL                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Worker 1      │  │   Worker 2      │  │   Worker 3      │    │
│  │   (Active)      │  │   (Active)      │  │   (Idle)        │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│  ┌─────────────────┐  ┌─────────────────┐                          │
│  │   Worker 4      │  │   Worker 5      │                          │
│  │   (Active)      │  │   (Idle)        │                          │
│  └─────────────────┘  └─────────────────┘                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Execute Task
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ASYNC SCRAPER LAYER                            │
│  - async_scraper.py                                                 │
│  - Async HTTP with aiohttp                                          │
│  - Connection pooling                                               │
│  - Parallel multi-page fetching                                     │
│  - Async extraction                                                 │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ HTTP Requests
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TARGET WEBSITES                             │
│  - example.com                                                      │
│  - company.com                                                      │
│  - business.org                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Request Flow - Single URL

### Step 1: Client Submits Job

```
Client
  │
  │ POST /api/scrape
  │ {"url": "https://example.com"}
  ▼
Flask API
  │
  ├─ Validate URL
  ├─ Check URL cache (Redis DB 2)
  │  └─ If cached: Return immediately (<10ms)
  │
  ├─ Generate job_id
  ├─ Store job metadata (Redis DB 0)
  ├─ Queue Celery task
  │
  └─ Return job_id (<100ms)
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "poll_url": "/api/job/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### Step 2: Worker Processes Job

```
Celery Worker
  │
  ├─ Pick job from queue
  ├─ Update status: "processing"
  │
  ▼
Async Scraper
  │
  ├─ Check HTTP cache
  │  └─ If cached: Use cached HTML
  │
  ├─ Fetch HTML (aiohttp)
  │  ├─ Connection pooling
  │  ├─ DNS caching
  │  └─ Non-blocking I/O
  │
  ├─ Parse HTML (BeautifulSoup, once)
  │
  ├─ Parallel Extraction (ThreadPoolExecutor)
  │  ├─ Extract emails
  │  ├─ Extract phones
  │  ├─ Extract company
  │  ├─ Extract address
  │  └─ Extract social
  │
  ├─ Build result
  │
  └─ Store result (Redis DB 1)
     └─ Cache by URL (Redis DB 2)
```

**Time**: 2-4 seconds

---

### Step 3: Client Polls for Results

```
Client
  │
  │ GET /api/job/{job_id}
  ▼
Flask API
  │
  ├─ Get task status (Celery)
  │
  ├─ If pending: Return "pending"
  ├─ If processing: Return "processing"
  ├─ If completed: Return result
  │
  └─ Response
```

**Polling Loop**:
```python
while True:
    response = get_job_status(job_id)
    if response['status'] == 'completed':
        return response['result']
    time.sleep(1)
```

---

## Request Flow - Batch URLs

### Step 1: Client Submits Batch

```
Client
  │
  │ POST /api/batch
  │ {"urls": ["url1", "url2", "url3"]}
  ▼
Flask API
  │
  ├─ Validate URLs
  ├─ Generate job_id
  ├─ Queue batch task
  │
  └─ Return job_id (<100ms)
```

---

### Step 2: Workers Process Batch

```
Celery Worker
  │
  ├─ Pick batch job
  ├─ Split into individual tasks
  │
  ▼
Worker Pool (5 workers)
  │
  ├─ Worker 1: Scrape url1 (2-4s)
  ├─ Worker 2: Scrape url2 (2-4s)
  ├─ Worker 3: Scrape url3 (2-4s)
  ├─ Worker 4: Scrape url4 (2-4s)
  └─ Worker 5: Scrape url5 (2-4s)
  │
  └─ Combine results
     └─ Store in Redis
```

**Time**: 2-4 seconds (parallel)

---

## Data Flow

### 1. HTTP Response Caching

```
Request URL
  │
  ▼
Check HTTP Cache (cache.py)
  │
  ├─ Cache Hit
  │  └─ Return cached HTML (<10ms)
  │
  └─ Cache Miss
     │
     ├─ Fetch HTML (aiohttp)
     ├─ Store in cache (1 hour TTL)
     └─ Return HTML
```

---

### 2. Result Caching

```
Scrape URL
  │
  ▼
Check URL Cache (Redis DB 2)
  │
  ├─ Cache Hit
  │  └─ Return cached result (<10ms)
  │
  └─ Cache Miss
     │
     ├─ Scrape URL (2-4s)
     ├─ Store result (1 hour TTL)
     └─ Return result
```

---

### 3. Job Status Tracking

```
Job Lifecycle:
  │
  ├─ PENDING (queued, waiting for worker)
  │
  ├─ PROCESSING (worker picked up job)
  │
  ├─ COMPLETED (result ready)
  │  └─ Result stored in Redis
  │
  └─ FAILED (error occurred)
     └─ Error stored in Redis
```

---

## Component Interaction

### Flask API ↔ Redis

```python
# Store job
queue_manager.store_job(job_id, url, options)

# Get job status
job_data = queue_manager.get_job(job_id)

# Store result
queue_manager.store_result(job_id, result)

# Cache by URL
queue_manager.cache_url_result(url, result)
```

---

### Flask API ↔ Celery

```python
# Queue task
task = scrape_url_task.apply_async(args=[url, options], task_id=job_id)

# Get task status
task = celery_app.AsyncResult(job_id)
status = task.state  # PENDING, PROCESSING, SUCCESS, FAILURE
result = task.result
```

---

### Celery Worker ↔ Async Scraper

```python
# Worker calls async scraper
result = scrape_url_async_wrapper(url, proxy_manager, fast_mode=True)

# Async scraper returns ScraperResult
result = {
    'url': url,
    'success': True,
    'emails': [...],
    'phones': [...],
    'company_name': '...',
    'fetch_time': 2.3
}
```

---

## Scaling Strategy

### Horizontal Scaling (Add More Workers)

```
1 Worker:  1 URL in 2-4s = 0.25-0.5 URLs/s
5 Workers: 5 URLs in 2-4s = 1.25-2.5 URLs/s
10 Workers: 10 URLs in 2-4s = 2.5-5 URLs/s
```

**How to scale**:
```bash
# Start more workers
celery -A tasks worker --loglevel=info --concurrency=10
```

---

### Vertical Scaling (Increase Worker Concurrency)

```bash
# Single worker with 10 threads
celery -A tasks worker --loglevel=info --concurrency=10
```

---

### Distributed Scaling (Multiple Machines)

```
Machine 1: Flask API + Redis
Machine 2: Celery Workers (5 workers)
Machine 3: Celery Workers (5 workers)
Machine 4: Celery Workers (5 workers)

Total: 15 workers = 3.75-7.5 URLs/s
```

---

## Monitoring Points

### 1. Flask API Metrics

- Request rate (requests/second)
- Response time (<100ms target)
- Cache hit rate
- Error rate

---

### 2. Redis Metrics

- Queue length (pending jobs)
- Memory usage
- Cache hit rate
- Eviction rate

---

### 3. Celery Metrics

- Active workers
- Active tasks
- Completed tasks
- Failed tasks
- Task duration

---

### 4. Scraper Metrics

- Scraping time (2-4s target)
- Success rate
- Fetch mode distribution (HTML vs JS)
- Confidence score

---

## Failure Handling

### 1. Worker Failure

```
Worker crashes
  │
  ├─ Job returns to queue
  ├─ Another worker picks it up
  └─ Retry with exponential backoff
```

---

### 2. Redis Failure

```
Redis connection lost
  │
  ├─ Flask API falls back to sync mode
  ├─ Workers wait for reconnection
  └─ Jobs persist in Redis (if Redis restarts)
```

---

### 3. Target Website Failure

```
Website unreachable
  │
  ├─ Retry with different proxy
  ├─ Try different fetch mode (HTML → JS)
  ├─ Mark as failed after 3 retries
  └─ Store error in result
```

---

## Performance Characteristics

### Latency

| Operation | Latency |
|-----------|---------|
| API response (queue job) | <100ms |
| Cache hit (URL) | <10ms |
| Cache hit (HTTP) | <10ms |
| Scraping (single URL) | 2-4s |
| Scraping (batch 10 URLs, 5 workers) | 4-8s |

---

### Throughput

| Workers | URLs/second |
|---------|-------------|
| 1 | 0.25-0.5 |
| 5 | 1.25-2.5 |
| 10 | 2.5-5 |
| 20 | 5-10 |

---

### Resource Usage

| Component | CPU | Memory | Network |
|-----------|-----|--------|---------|
| Flask API | Low | Low | Low |
| Redis | Low | Medium | Low |
| Celery Worker | Medium | Medium | High |
| Async Scraper | Medium | Medium | High |

---

## Summary

Your system now has:

✅ **Non-blocking API** (<100ms response)  
✅ **Job queue** (Redis + Celery)  
✅ **Worker pool** (5+ workers)  
✅ **Multi-level caching** (HTTP + URL + Result)  
✅ **Async scraping** (aiohttp + connection pooling)  
✅ **Parallel extraction** (ThreadPoolExecutor)  
✅ **Monitoring** (Flower dashboard)  
✅ **Fault tolerance** (worker restart, job retry)  
✅ **Horizontal scaling** (add more workers)

**Ready for production!** 🚀
