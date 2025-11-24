# Phase 3 Quick Setup Guide

## Prerequisites

1. Python 3.8+
2. Redis server
3. All Phase 1 & 2 dependencies

---

## Installation Steps

### Step 1: Install Redis

**Windows (WSL)**:
```bash
wsl sudo apt-get update
wsl sudo apt-get install redis-server
```

**Linux**:
```bash
sudo apt-get install redis-server
```

**Mac**:
```bash
brew install redis
```

---

### Step 2: Install Python Dependencies

```bash
pip install -r requirements_phase3.txt
```

This installs:
- redis (Python client)
- celery (task queue)
- flower (monitoring dashboard)

---

### Step 3: Start Redis Server

**Terminal 1**:
```bash
# Windows (WSL)
wsl redis-server

# Linux/Mac
redis-server
```

Verify it's running:
```bash
redis-cli ping
# Should return: PONG
```

---

### Step 4: Start Celery Workers

**Terminal 2**:
```bash
# Windows (requires eventlet)
pip install eventlet
celery -A tasks worker --loglevel=info --pool=eventlet

# Linux/Mac
celery -A tasks worker --loglevel=info --concurrency=5
```

You should see:
```
[tasks]
  . tasks.scrape_url_task
  . tasks.scrape_batch_task

[2024-11-24 12:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-11-24 12:00:00,000: INFO/MainProcess] celery@hostname ready.
```

---

### Step 5: Start Flask API

**Terminal 3**:
```bash
python app_queue.py
```

You should see:
```
INFO:__main__:Redis connected - queue system ready
INFO:__main__:Celery available - background processing enabled
 * Running on http://0.0.0.0:5000
```

---

### Step 6: (Optional) Start Flower Monitoring

**Terminal 4**:
```bash
celery -A tasks flower
```

Visit: http://localhost:5555

---

## Quick Test

### Test 1: Single URL

```bash
# Queue job
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Response (instant):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "poll_url": "/api/job/550e8400-e29b-41d4-a716-446655440000"
}

# Poll for results
curl http://localhost:5000/api/job/550e8400-e29b-41d4-a716-446655440000
```

---

### Test 2: Check Queue Stats

```bash
curl http://localhost:5000/api/queue/stats
```

Response:
```json
{
  "pending": 0,
  "processing": 1,
  "completed": 5,
  "failed": 0,
  "total": 6,
  "workers": 5,
  "active_tasks": 1
}
```

---

## Architecture Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/scrape
       ▼
┌─────────────┐
│  Flask API  │ <100ms response
└──────┬──────┘
       │ Queue job
       ▼
┌─────────────┐
│    Redis    │
│  Job Queue  │
└──────┬──────┘
       │ Pick job
       ▼
┌─────────────┐
│   Celery    │
│   Workers   │ 2-4s scraping
│  (5 workers)│
└──────┬──────┘
       │ Store result
       ▼
┌─────────────┐
│    Redis    │
│Result Cache │
└──────┬──────┘
       │ Poll
       ▼
┌─────────────┐
│   Client    │
│   Result    │
└─────────────┘
```

---

## Performance

- **API Response**: <100ms (instant job queuing)
- **Scraping Time**: 2-4 seconds per URL
- **Throughput**: 5 workers = 1.25-2.5 URLs/second
- **Cache Hit**: <10ms (instant for repeated URLs)

---

## Troubleshooting

### Redis not connecting?
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server
```

### Celery workers not starting?
```bash
# Windows: Install eventlet
pip install eventlet
celery -A tasks worker --pool=eventlet --loglevel=info

# Linux/Mac: Use default pool
celery -A tasks worker --loglevel=info
```

### Job stuck in pending?
```bash
# Check if workers are running
celery -A tasks inspect active

# Restart workers
celery -A tasks worker --loglevel=info
```

---

## What's Next?

Phase 3 is complete! You now have:
- ✅ Non-blocking API
- ✅ Job queue system
- ✅ Worker pool
- ✅ Result caching
- ✅ Monitoring dashboard

**Next**: Phase 4 (Advanced Optimizations) for even better performance!
