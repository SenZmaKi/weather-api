# Deployment Guide

This guide covers deploying the Weather API service to production environments, including best practices, configuration, and monitoring.

## Quick Deploy Options

- [Docker Deployment](#docker-deployment)
- [Traditional Server](#traditional-server-deployment)
- [Cloud Platforms](#cloud-platform-deployment)
- [Container Orchestration](#container-orchestration)

## Prerequisites

### Required
- Python 3.12+
- OpenWeatherMap API key
- Domain name (for production)
- SSL certificate (for HTTPS)

### Recommended
- Reverse proxy (nginx/Apache)
- Process manager (systemd/supervisor)
- Database backup solution
- Monitoring tools

## Environment Configuration

### Production Environment Variables

Create a production `.env` file:

```bash
# Production .env
# OpenWeatherMap API Configuration
OPENWEATHER_API_KEY=your_production_api_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5

# Database Configuration (PostgreSQL recommended for production)
DATABASE_URL=postgresql+asyncpg://username:password@localhost/weatherapi

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=False

# Security
CORS_ORIGINS=["https://yourdomain.com", "https://api.yourdomain.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Additional Production Settings
LOG_LEVEL=INFO
WORKERS=4
```

### Security Checklist

- [ ] API key stored securely (not in code)
- [ ] Debug mode disabled (`DEBUG=False`)
- [ ] CORS origins restricted (no wildcards)
- [ ] Database credentials secured
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Log levels appropriate
- [ ] File permissions set correctly

## Docker Deployment

### Option 1: Single Container

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
# Build image
docker build -t weather-api:latest .

# Run container
docker run -d \
  --name weather-api \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  weather-api:latest
```

### Option 2: Multi-Container with Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/weatherapi
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - weather-network

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: weatherapi
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - weather-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./static:/var/www/static
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - weather-network

volumes:
  postgres_data:

networks:
  weather-network:
    driver: bridge
```

**nginx.conf:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream weather_app {
        server app:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API endpoints
        location /weather {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://weather_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check (no rate limiting)
        location /health {
            proxy_pass http://weather_app;
            proxy_set_header Host $host;
        }

        # Main application
        location / {
            proxy_pass http://weather_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

**Deploy with compose:**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale app instances
docker-compose up -d --scale app=3

# Stop services
docker-compose down
```

## Traditional Server Deployment

### Ubuntu/Debian Server Setup

**1. Install dependencies:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Install other dependencies
sudo apt install -y nginx postgresql postgresql-contrib git curl
```

**2. Create application user:**
```bash
# Create dedicated user
sudo useradd --create-home --shell /bin/bash weatherapi
sudo usermod -aG sudo weatherapi

# Switch to app user
sudo -u weatherapi -i
```

**3. Deploy application:**
```bash
# Clone repository
git clone https://github.com/SenZmaKi/weather-api.git
cd weather-api

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
nano .env  # Edit with production values
```

**4. Configure PostgreSQL:**
```bash
# Switch to postgres user
sudo -u postgres -i

# Create database and user
createdb weatherapi
createuser --interactive weatherapi

# Set password
psql
\password weatherapi
\q

# Grant permissions
psql weatherapi
GRANT ALL PRIVILEGES ON DATABASE weatherapi TO weatherapi;
\q
```

**5. Create systemd service:**

**/etc/systemd/system/weather-api.service:**
```ini
[Unit]
Description=Weather API Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=weatherapi
Group=weatherapi
WorkingDirectory=/home/weatherapi/weather-api
Environment=PATH=/home/weatherapi/weather-api/.venv/bin
ExecStart=/home/weatherapi/weather-api/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**6. Configure nginx:**

**/etc/nginx/sites-available/weather-api:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

    location /static/ {
        alias /home/weatherapi/weather-api/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**7. Enable and start services:**
```bash
# Enable nginx site
sudo ln -s /etc/nginx/sites-available/weather-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Enable and start weather API
sudo systemctl enable weather-api
sudo systemctl start weather-api

# Check status
sudo systemctl status weather-api
```

## Cloud Platform Deployment

### AWS Deployment (ECS + RDS)

**1. Create Dockerfile (optimized for AWS):**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install uv

# Copy and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**2. Create task definition:**
```json
{
  "family": "weather-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "weather-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/weather-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql+asyncpg://username:password@rds-endpoint:5432/weatherapi"
        }
      ],
      "secrets": [
        {
          "name": "OPENWEATHER_API_KEY",
          "valueFrom": "arn:aws:ssm:region:account:parameter/weather-api/api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/weather-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

**1. Create cloudbuild.yaml:**
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/weather-api', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/weather-api']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'weather-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/weather-api'
      - '--platform'
      - 'managed'
      - '--region'
      - 'us-central1'
      - '--allow-unauthenticated'
      - '--port'
      - '8000'
      - '--set-env-vars'
      - 'DATABASE_URL=postgresql+asyncpg://user:pass@/db?host=/cloudsql/project:region:instance'
      - '--set-secrets'
      - 'OPENWEATHER_API_KEY=weather-api-key:latest'
```

**2. Deploy:**
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Heroku Deployment

**1. Create Procfile:**
```
web: uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**2. Create runtime.txt:**
```
python-3.12.0
```

**3. Deploy:**
```bash
# Install Heroku CLI
# Login and create app
heroku create weather-api-yourname

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set OPENWEATHER_API_KEY=your_key_here
heroku config:set DEBUG=False

# Deploy
git push heroku main
```

## Container Orchestration

### Kubernetes Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-api
  labels:
    app: weather-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: weather-api
  template:
    metadata:
      labels:
        app: weather-api
    spec:
      containers:
      - name: weather-api
        image: weather-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: weather-api-secrets
              key: database-url
        - name: OPENWEATHER_API_KEY
          valueFrom:
            secretKeyRef:
              name: weather-api-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: weather-api-service
spec:
  selector:
    app: weather-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: weather-api-secrets
type: Opaque
data:
  database-url: <base64-encoded-url>
  api-key: <base64-encoded-key>
```

**Deploy:**
```bash
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### CloudFlare SSL

For CloudFlare proxy:
```nginx
# Origin certificate from CloudFlare
ssl_certificate /etc/ssl/certs/cloudflare-origin.pem;
ssl_certificate_key /etc/ssl/private/cloudflare-origin.key;

# Trust CloudFlare IPs
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
real_ip_header CF-Connecting-IP;
```

## Database Management

### PostgreSQL Production Setup

**1. Install and configure:**
```bash
sudo apt install postgresql postgresql-contrib

# Configure PostgreSQL
sudo -u postgres psql
```

```sql
-- Create database and user
CREATE DATABASE weatherapi;
CREATE USER weatherapi WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE weatherapi TO weatherapi;

-- Performance settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
```

**2. Backup strategy:**
```bash
#!/bin/bash
# backup-weather-api.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/weather-api"
DB_NAME="weatherapi"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump $DB_NAME | gzip > "$BACKUP_DIR/weather-api-$DATE.sql.gz"

# Keep only last 7 days
find $BACKUP_DIR -name "weather-api-*.sql.gz" -mtime +7 -delete

# Add to crontab:
# 0 2 * * * /path/to/backup-weather-api.sh
```

### Database Migrations (Future)

For production migrations, consider using Alembic:

```bash
# Install Alembic
uv add alembic

# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

## Monitoring and Logging

### Application Logs

**Configure structured logging:**
```python
# app/logging.py
import logging
import sys
from typing import Dict, Any

def configure_logging(log_level: str = "INFO") -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
```

**Log aggregation with ELK Stack:**

**docker-compose.logging.yml:**
```yaml
services:
  elasticsearch:
    image: elasticsearch:8.7.1
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  logstash:
    image: logstash:8.7.1
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:8.7.1
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### Health Monitoring

**Enhanced health check:**
```python
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check."""
    health_data = {
        "status": "healthy",
        "service": "Weather API",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    
    # Database check
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
        health_data["database"] = "healthy"
    except Exception as e:
        health_data["database"] = f"unhealthy: {str(e)}"
        health_data["status"] = "unhealthy"
    
    # External API check
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("https://api.openweathermap.org/data/2.5/weather?q=London&appid=test")
        health_data["external_api"] = "reachable" if response.status_code != 401 else "authentication_required"
    except Exception as e:
        health_data["external_api"] = f"unreachable: {str(e)}"
    
    return health_data
```

### Prometheus Metrics

```bash
# Install prometheus client
uv add prometheus-client
```

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('weather_api_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('weather_api_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Performance Optimization

### Application Tuning

**1. Uvicorn workers:**
```bash
# Single machine deployment
uvicorn app.main:app --workers $(nproc) --host 0.0.0.0 --port 8000

# Or use gunicorn with uvicorn workers
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**2. Database connection pooling:**
```python
# app/models/database.py
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**3. HTTP client optimization:**
```python
# app/services/weather_service.py
class WeatherService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
```

### Caching Strategy

**Redis caching:**
```python
import redis.asyncio as redis

class CacheService:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379")
    
    async def get_weather_cache(self, city: str) -> Optional[Dict]:
        """Get cached weather data."""
        cached = await self.redis.get(f"weather:{city}")
        return json.loads(cached) if cached else None
    
    async def set_weather_cache(self, city: str, data: Dict, ttl: int = 300):
        """Cache weather data for 5 minutes."""
        await self.redis.setex(f"weather:{city}", ttl, json.dumps(data))
```

## Troubleshooting

### Common Issues

**1. Database connection errors:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Reset connections
sudo systemctl restart postgresql
```

**2. SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL configuration
curl -I https://yourdomain.com
```

**3. Rate limiting issues:**
```bash
# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Adjust rate limits in nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=120r/m;
```

**4. High memory usage:**
```bash
# Monitor memory usage
htop
free -h

# Reduce uvicorn workers
# Check for memory leaks in application code
```

### Log Analysis

**Common log patterns:**
```bash
# Monitor application logs
journalctl -u weather-api -f

# Check for errors
journalctl -u weather-api | grep ERROR

# Monitor nginx access logs
tail -f /var/log/nginx/access.log | grep weather-api

# Monitor error rates
grep "HTTP/1.1\" 5" /var/log/nginx/access.log | wc -l
```

## Backup and Recovery

### Complete Backup Strategy

**1. Database backups (daily):**
```bash
#!/bin/bash
pg_dump weatherapi | gzip > /backups/db-$(date +%Y%m%d).sql.gz
```

**2. Application backups (weekly):**
```bash
#!/bin/bash
tar -czf /backups/app-$(date +%Y%m%d).tar.gz /home/weatherapi/weather-api
```

**3. SSL certificates backup:**
```bash
#!/bin/bash
cp -r /etc/letsencrypt /backups/letsencrypt-$(date +%Y%m%d)
```

### Disaster Recovery

**Recovery procedures:**

1. **Database recovery:**
```bash
# Restore from backup
gunzip -c /backups/db-YYYYMMDD.sql.gz | psql weatherapi
```

2. **Application recovery:**
```bash
# Extract application backup
tar -xzf /backups/app-YYYYMMDD.tar.gz -C /

# Restart services
sudo systemctl restart weather-api nginx
```

3. **SSL certificate recovery:**
```bash
# Restore certificates
cp -r /backups/letsencrypt-YYYYMMDD /etc/letsencrypt
sudo systemctl restart nginx
```

This deployment guide provides comprehensive instructions for deploying the Weather API service in various environments, from simple single-server setups to complex cloud deployments with monitoring and high availability.