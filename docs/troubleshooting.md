# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Weather API service.

## Quick Diagnostics

### Health Check
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{"status": "healthy", "service": "Weather API"}
```

### Service Status
```bash
# Check if service is running
sudo systemctl status weather-api

# View recent logs
sudo journalctl -u weather-api --since "5 minutes ago"
```

### Database Connectivity
```bash
# Test database connection
python -c "
from app.config import get_settings
from sqlalchemy import create_engine
engine = create_engine(get_settings().database_url.replace('sqlite+aiosqlite', 'sqlite'))
print('Database connection:', 'OK' if engine.connect() else 'FAILED')
"
```

## Common Issues

### 1. Service Won't Start

#### Symptom
```bash
$ uv run uvicorn app.main:app
ImportError: No module named 'app'
```

#### Diagnosis
```bash
# Check current directory
pwd
# Should be in the weather-api root directory

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check if dependencies are installed
uv run python -c "import fastapi; print('FastAPI OK')"
```

#### Solutions

**Wrong directory:**
```bash
cd /path/to/weather-api
uv run uvicorn app.main:app --reload
```

**Missing dependencies:**
```bash
uv sync
```

**Python path issues:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run uvicorn app.main:app --reload
```

### 2. Database Connection Errors

#### Symptom
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked
```

#### Diagnosis
```bash
# Check if database file exists and permissions
ls -la weather.db

# Check for other processes using the database
sudo lsof weather.db

# Check disk space
df -h .
```

#### Solutions

**Database locked:**
```bash
# Stop all instances of the application
sudo systemctl stop weather-api
pkill -f uvicorn

# Remove lock (if safe)
rm weather.db-shm weather.db-wal 2>/dev/null

# Restart service
sudo systemctl start weather-api
```

**Permission issues:**
```bash
# Fix permissions
sudo chown weatherapi:weatherapi weather.db
chmod 644 weather.db
```

**Corrupted database:**
```bash
# Backup and recreate
cp weather.db weather.db.backup
rm weather.db
uv run uvicorn app.main:app --reload  # This will recreate the database
```

### 3. OpenWeatherMap API Issues

#### Symptom
```json
{
  "error": "HTTPStatusError",
  "message": "Failed to fetch weather data: 401 Unauthorized",
  "status_code": 500
}
```

#### Diagnosis
```bash
# Check if API key is set
echo $OPENWEATHER_API_KEY
# Or check .env file
grep OPENWEATHER_API_KEY .env

# Test API key manually
curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_API_KEY"
```

#### Solutions

**Missing API key:**
```bash
# Set in .env file
echo "OPENWEATHER_API_KEY=your_actual_key_here" >> .env

# Restart application
sudo systemctl restart weather-api
```

**Invalid API key:**
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Generate a new API key
3. Update `.env` file
4. Restart application

**Rate limit exceeded:**
```bash
# Check rate limiting configuration
grep RATE_LIMIT .env

# Temporarily increase limits (if needed)
echo "RATE_LIMIT_PER_MINUTE=120" >> .env
```

### 4. High CPU Usage

#### Symptom
```bash
$ top
# Shows high CPU usage for uvicorn/python processes
```

#### Diagnosis
```bash
# Monitor CPU usage
htop

# Check worker processes
ps aux | grep uvicorn

# Check for infinite loops in logs
sudo journalctl -u weather-api | grep -i error

# Profile the application (if needed)
uv add py-spy
py-spy top --pid $(pgrep -f uvicorn)
```

#### Solutions

**Too many workers:**
```bash
# Reduce number of workers
uvicorn app.main:app --workers 2 --host 0.0.0.0 --port 8000

# Or in systemd service file
ExecStart=/path/to/uvicorn app.main:app --workers 2 --host 0.0.0.0 --port 8000
```

**Infinite loops in code:**
- Check recent code changes
- Review error logs for patterns
- Add debugging statements to identify the issue

**External API timeouts:**
```python
# In app/services/weather_service.py
async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
    # Your API calls
```

### 5. Memory Leaks

#### Symptom
```bash
$ free -h
# Shows continuously increasing memory usage
```

#### Diagnosis
```bash
# Monitor memory usage over time
while true; do
    ps -p $(pgrep -f uvicorn) -o pid,ppid,cmd,%mem,%cpu
    sleep 30
done

# Check for database connection leaks
sudo ss -tuln | grep 5432  # PostgreSQL
```

#### Solutions

**Database connection leaks:**
```python
# Ensure proper session handling
async def get_weather(db: AsyncSession = Depends(get_db)):
    try:
        # Your logic here
        return result
    finally:
        await db.close()  # Explicitly close if needed
```

**HTTP client leaks:**
```python
# Use context managers
async with httpx.AsyncClient() as client:
    response = await client.get(url)
    # Client automatically closed
```

**Restart service periodically:**
```bash
# Add to crontab for temporary workaround
0 4 * * * /bin/systemctl restart weather-api
```

### 6. Port Already in Use

#### Symptom
```
OSError: [Errno 98] Address already in use
```

#### Diagnosis
```bash
# Check what's using port 8000
sudo netstat -tulpn | grep :8000
# Or
sudo ss -tulpn | grep :8000

# Find process ID
sudo lsof -i :8000
```

#### Solutions

**Kill existing process:**
```bash
# Kill by PID
sudo kill -9 <PID>

# Kill by process name
sudo pkill -f uvicorn
```

**Use different port:**
```bash
uv run uvicorn app.main:app --port 8001
```

**Find available port:**
```bash
# Check for available ports
for port in {8000..8010}; do
    (echo >/dev/tcp/localhost/$port) >/dev/null 2>&1 || echo "Port $port is available"
done
```

### 7. SSL Certificate Issues

#### Symptom
```
SSL certificate verify failed
```

#### Diagnosis
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout -dates

# Test SSL connection
openssl s_client -connect yourdomain.com:443

# Check certificate chain
curl -I https://yourdomain.com
```

#### Solutions

**Expired certificate:**
```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Restart nginx
sudo systemctl restart nginx
```

**Wrong certificate path:**
```nginx
# Check nginx configuration
server {
    ssl_certificate /correct/path/to/cert.pem;
    ssl_certificate_key /correct/path/to/key.pem;
}
```

**Certificate chain issues:**
```bash
# Use full chain certificate
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
```

### 8. Rate Limiting Issues

#### Symptom
```json
{
  "error": "Rate limit exceeded",
  "status_code": 429
}
```

#### Diagnosis
```bash
# Check rate limiting configuration
grep -r "rate" /etc/nginx/

# Check rate limiting logs
sudo grep "limiting requests" /var/log/nginx/error.log

# Monitor request rates
sudo tail -f /var/log/nginx/access.log | grep -E "HTTP/[0-9.]+ (429|200)"
```

#### Solutions

**Adjust nginx rate limits:**
```nginx
# Increase rate limits in nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=120r/m;
limit_req zone=api burst=30 nodelay;
```

**Implement application-level caching:**
```python
# Cache responses to reduce API calls
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_cached_weather(city: str, cache_time: int):
    # Cache for 5 minutes
    return get_weather_from_api(city)

# Use cache_time = int(datetime.now().timestamp() / 300)
```

**Whitelist trusted IPs:**
```nginx
# In nginx configuration
geo $limited {
    default 1;
    192.168.1.0/24 0;  # Office network
    10.0.0.0/8 0;      # Internal network
}

map $limited $limit {
    1 $binary_remote_addr;
    0 "";
}

limit_req_zone $limit zone=api:10m rate=60r/m;
```

## Error Code Reference

### HTTP Status Codes

| Code | Meaning | Common Causes | Solutions |
|------|---------|---------------|-----------|
| 400 | Bad Request | Missing required parameters | Check API documentation for required fields |
| 401 | Unauthorized | Invalid API key | Verify OpenWeatherMap API key |
| 404 | Not Found | Invalid city name, route not found | Check spelling, verify endpoint exists |
| 429 | Too Many Requests | Rate limit exceeded | Implement caching, reduce request frequency |
| 500 | Internal Server Error | Database issues, external API failure | Check logs, verify dependencies |
| 503 | Service Unavailable | Service overloaded, maintenance | Check system resources, restart service |

### Application Error Codes

#### Database Errors
```python
# Connection timeout
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached

# Solution: Increase pool size
engine = create_async_engine(url, pool_size=20, max_overflow=30)
```

#### External API Errors
```python
# OpenWeatherMap API errors
httpx.HTTPStatusError: 401 Unauthorized  # Invalid API key
httpx.HTTPStatusError: 404 Not Found     # City not found
httpx.HTTPStatusError: 429 Too Many Requests  # Rate limit exceeded
httpx.ConnectTimeout: Connection timeout  # Network issues
```

## Performance Issues

### Slow API Responses

#### Diagnosis
```bash
# Test response times
time curl "http://localhost:8000/weather?city=London"

# Monitor with multiple requests
for i in {1..10}; do
    time curl -s "http://localhost:8000/weather?city=London" >/dev/null
done
```

#### Solutions

**Database optimization:**
```sql
-- Add indexes
CREATE INDEX IF NOT EXISTS idx_search_history_city ON search_history(city);
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(timestamp DESC);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM search_history ORDER BY timestamp DESC LIMIT 10;
```

**HTTP client optimization:**
```python
# Use connection pooling
client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)
```

**Caching layer:**
```python
# Add Redis caching
import redis.asyncio as redis

async def get_weather_with_cache(city: str):
    cache_key = f"weather:{city}"
    cached = await redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    weather = await fetch_weather(city)
    
    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(weather))
    
    return weather
```

### High Memory Usage

#### Diagnosis
```bash
# Monitor memory usage
ps -p $(pgrep -f uvicorn) -o pid,ppid,%mem,vsz,rss,cmd

# Check for memory leaks
valgrind --tool=memcheck --leak-check=full python -m app.main
```

#### Solutions

**Optimize database queries:**
```python
# Use select specific columns
result = await db.execute(
    select(SearchHistory.id, SearchHistory.city, SearchHistory.timestamp)
    .order_by(SearchHistory.timestamp.desc())
    .limit(100)
)
```

**Implement pagination:**
```python
# Limit large queries
@router.get("/history")
async def get_history(
    limit: int = Query(50, le=1000),  # Maximum 1000 records
    offset: int = Query(0, ge=0)
):
    # Implementation with limits
```

## Debugging Tools

### Application Debugging

**Enable debug mode:**
```bash
# In .env file
DEBUG=True

# Run with debug
uv run uvicorn app.main:app --reload --log-level debug
```

**Add logging:**
```python
import logging

logger = logging.getLogger(__name__)

@router.get("/weather")
async def get_weather(city: str):
    logger.info(f"Weather request for city: {city}")
    try:
        result = await weather_service.get_weather(city)
        logger.info(f"Weather data retrieved successfully for {city}")
        return result
    except Exception as e:
        logger.error(f"Error getting weather for {city}: {str(e)}")
        raise
```

**Interactive debugging:**
```python
# Add breakpoints with pdb
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

### Network Debugging

**Monitor HTTP requests:**
```bash
# Log all HTTP requests
sudo tcpdump -i any -A -s 0 'host api.openweathermap.org'

# Monitor with netstat
watch 'netstat -an | grep :8000'
```

**Test external API:**
```bash
# Test OpenWeatherMap API directly
curl -v "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY"

# Check DNS resolution
nslookup api.openweathermap.org

# Test connectivity
telnet api.openweathermap.org 443
```

### Database Debugging

**SQLite debugging:**
```bash
# Open database directly
sqlite3 weather.db

# Check tables
.tables

# Check schema
.schema search_history

# Query data
SELECT COUNT(*) FROM search_history;
SELECT * FROM search_history ORDER BY timestamp DESC LIMIT 5;
```

**PostgreSQL debugging:**
```bash
# Connect to database
psql -h localhost -U weatherapi weatherapi

# Check connections
SELECT * FROM pg_stat_activity WHERE datname = 'weatherapi';

# Check table sizes
SELECT schemaname,tablename,attname,n_distinct,correlation FROM pg_stats;

# Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC;
```

## Log Analysis

### Log Locations

**Application logs:**
```bash
# Systemd service logs
sudo journalctl -u weather-api -f

# Docker container logs
docker logs weather-api -f

# Manual logs (if configured)
tail -f /var/log/weather-api/app.log
```

**Web server logs:**
```bash
# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs  
tail -f /var/log/nginx/error.log

# Apache logs
tail -f /var/log/apache2/access.log
```

### Log Analysis Commands

**Error patterns:**
```bash
# Find all errors in last hour
journalctl -u weather-api --since "1 hour ago" | grep -i error

# Count error types
journalctl -u weather-api --since "1 day ago" | grep -i error | sort | uniq -c

# Find high error rate periods
journalctl -u weather-api --since "1 day ago" | grep -i error | cut -d' ' -f1-3 | uniq -c
```

**Performance analysis:**
```bash
# Response time analysis from nginx logs
awk '{print $NF}' /var/log/nginx/access.log | sort -n | tail -20

# Request frequency analysis
awk '{print $4}' /var/log/nginx/access.log | cut -d: -f2 | sort | uniq -c

# Status code distribution
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c
```

## Prevention Best Practices

### Monitoring Setup

**Health checks:**
```bash
# Set up health check monitoring
# Add to crontab:
*/5 * * * * curl -f http://localhost:8000/health || echo "Service down!" | mail -s "Weather API Alert" admin@example.com
```

**Log rotation:**
```bash
# Configure logrotate for application logs
# /etc/logrotate.d/weather-api
/var/log/weather-api/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 weatherapi weatherapi
    postrotate
        systemctl reload weather-api
    endscript
}
```

### Automated Testing

**Health monitoring script:**
```python
#!/usr/bin/env python3
import asyncio
import httpx
import json
import sys
from datetime import datetime

async def test_endpoints():
    """Test all critical endpoints."""
    base_url = "http://localhost:8000"
    tests = [
        ("GET", "/health", None),
        ("GET", "/weather?city=London", None),
        ("GET", "/weather/forecast?city=London&days=3", None),
        ("GET", "/weather/history?limit=5", None),
    ]
    
    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        for method, endpoint, data in tests:
            try:
                start_time = datetime.now()
                if method == "GET":
                    response = await client.get(f"{base_url}{endpoint}")
                else:
                    response = await client.post(f"{base_url}{endpoint}", json=data)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                results.append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "duration": duration,
                    "success": response.status_code < 400
                })
                
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "status": 0,
                    "duration": 0,
                    "success": False,
                    "error": str(e)
                })
    
    # Print results
    all_passed = all(r["success"] for r in results)
    for result in results:
        status = "✓" if result["success"] else "✗"
        print(f"{status} {result['endpoint']} - {result['status']} ({result['duration']:.2f}s)")
        if not result["success"] and "error" in result:
            print(f"  Error: {result['error']}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(test_endpoints())
    sys.exit(0 if success else 1)
```

**Add to crontab:**
```bash
# Test every 15 minutes
*/15 * * * * /usr/local/bin/weather-api-test.py || echo "Health check failed" | mail -s "Weather API Alert" admin@example.com
```

This troubleshooting guide provides comprehensive solutions for the most common issues you might encounter with the Weather API service, from basic connectivity problems to complex performance issues.