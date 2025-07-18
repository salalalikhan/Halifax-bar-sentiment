# Deployment Guide

This guide covers deploying the Halifax Bar Sentiment Analysis system to production.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM recommended
- **Storage**: 50GB+ available space
- **Network**: Stable internet connection

### Software Dependencies
- **Python**: 3.11+
- **PostgreSQL**: 13+
- **Redis**: 6+ (for caching and job queues)
- **Docker**: 20.10+ (optional but recommended)
- **Node.js**: 16+ (for dashboard)
- **Nginx**: 1.18+ (for reverse proxy)

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/halifax_bar_sentiment.git
cd halifax_bar_sentiment
```

#### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your configuration
```

#### 3. Build and Deploy
```bash
# Build all services
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Option 2: Manual Deployment

#### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql postgresql-contrib redis-server
sudo apt install -y nginx supervisor
sudo apt install -y nodejs npm
```

#### 2. Database Setup
```bash
# Create database user
sudo -u postgres psql -c "CREATE USER halifax_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "CREATE DATABASE halifax_bars OWNER halifax_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE halifax_bars TO halifax_user;"
```

#### 3. Application Setup
```bash
# Create application directory
sudo mkdir -p /opt/halifax_sentiment
sudo chown $USER:$USER /opt/halifax_sentiment
cd /opt/halifax_sentiment

# Clone repository
git clone https://github.com/yourusername/halifax_bar_sentiment.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dashboard dependencies
cd src/dashboard
npm install
npm run build
cd ../..
```

#### 4. Configuration
```bash
# Copy environment file
cp env.example .env

# Edit configuration
nano .env
```

Required environment variables:
```bash
# Database Configuration
POSTGRES_DBNAME=halifax_bars
POSTGRES_USER=halifax_user
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Reddit API Configuration
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=Halifax Bar Analytics

# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here

# Security Configuration
ALLOWED_HOSTS=your-domain.com,localhost
CORS_ORIGINS=https://your-domain.com
```

#### 5. Database Migration
```bash
# Run database migrations
python -m alembic upgrade head

# Create initial data
python scripts/setup_initial_data.py
```

#### 6. Process Management with Supervisor
```bash
# Create supervisor configuration
sudo nano /etc/supervisor/conf.d/halifax_sentiment.conf
```

```ini
[program:halifax_api]
command=/opt/halifax_sentiment/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/opt/halifax_sentiment
user=halifax_user
autostart=true
autorestart=true
stdout_logfile=/var/log/halifax_sentiment/api.log
stderr_logfile=/var/log/halifax_sentiment/api_error.log
environment=PATH="/opt/halifax_sentiment/venv/bin"

[program:halifax_worker]
command=/opt/halifax_sentiment/venv/bin/python -m celery -A src.worker worker --loglevel=info
directory=/opt/halifax_sentiment
user=halifax_user
autostart=true
autorestart=true
stdout_logfile=/var/log/halifax_sentiment/worker.log
stderr_logfile=/var/log/halifax_sentiment/worker_error.log
environment=PATH="/opt/halifax_sentiment/venv/bin"
```

```bash
# Create log directory
sudo mkdir -p /var/log/halifax_sentiment
sudo chown halifax_user:halifax_user /var/log/halifax_sentiment

# Create user
sudo useradd -r -s /bin/false halifax_user

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start halifax_api halifax_worker
```

#### 7. Nginx Configuration
```bash
# Create nginx configuration
sudo nano /etc/nginx/sites-available/halifax_sentiment
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Dashboard
    location / {
        root /opt/halifax_sentiment/src/dashboard/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Static files
    location /static/ {
        root /opt/halifax_sentiment/src/dashboard/build;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/halifax_sentiment /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring Setup

### 1. System Monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop netstat-nat

# Setup log rotation
sudo nano /etc/logrotate.d/halifax_sentiment
```

```
/var/log/halifax_sentiment/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su halifax_user halifax_user
}
```

### 2. Application Monitoring
The application includes built-in monitoring endpoints:

- Health: `/monitoring/health/detailed`
- Metrics: `/monitoring/metrics`
- Performance: `/monitoring/performance`
- Alerts: `/monitoring/alerts`
- Dashboard: `/monitoring/dashboard`

### 3. Database Monitoring
```bash
# Install PostgreSQL monitoring
sudo apt install -y postgresql-contrib

# Enable monitoring
sudo -u postgres psql -c "CREATE EXTENSION pg_stat_statements;"
```

## Backup Strategy

### Database Backup
```bash
# Create backup script
nano /opt/halifax_sentiment/scripts/backup_db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/halifax_sentiment"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/halifax_bars_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U halifax_user -d halifax_bars | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

```bash
# Make executable
chmod +x /opt/halifax_sentiment/scripts/backup_db.sh

# Schedule daily backup
crontab -e
# Add: 0 2 * * * /opt/halifax_sentiment/scripts/backup_db.sh
```

### Application Backup
```bash
# Create application backup script
nano /opt/halifax_sentiment/scripts/backup_app.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/halifax_sentiment"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/halifax_sentiment"

mkdir -p $BACKUP_DIR

# Backup configuration and logs
tar -czf "$BACKUP_DIR/app_config_$DATE.tar.gz" \
    "$APP_DIR/.env" \
    "$APP_DIR/logs/" \
    /etc/supervisor/conf.d/halifax_sentiment.conf \
    /etc/nginx/sites-available/halifax_sentiment

# Keep only last 30 days
find $BACKUP_DIR -type f -name "app_config_*.tar.gz" -mtime +30 -delete

echo "Application backup completed: $BACKUP_DIR/app_config_$DATE.tar.gz"
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Configure UFW
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 8000/tcp  # Block direct API access
```

### 2. Database Security
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/13/main/postgresql.conf
```

```
# Listen only on localhost
listen_addresses = 'localhost'

# Enable logging
log_statement = 'all'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### 3. Application Security
- Use environment variables for sensitive data
- Enable CORS restrictions
- Implement rate limiting
- Use HTTPS everywhere
- Regular security updates

## Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_mentions_bar_name ON mentions(bar_name);
CREATE INDEX idx_mentions_created_at ON mentions(created_at);
CREATE INDEX idx_mentions_sentiment ON mentions(sentiment_score);
```

### 2. Application Optimization
```bash
# Optimize Python settings
export PYTHONHASHSEED=0
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
```

### 3. Nginx Optimization
```nginx
# Add to nginx configuration
client_max_body_size 10M;
client_body_timeout 60s;
keepalive_timeout 65s;
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

## Troubleshooting

### Common Issues

#### 1. Service Not Starting
```bash
# Check logs
sudo journalctl -u supervisor -f
sudo supervisorctl tail halifax_api
sudo supervisorctl tail halifax_worker

# Check configuration
sudo supervisorctl status
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U halifax_user -d halifax_bars -c "SELECT 1;"
```

#### 3. High Memory Usage
```bash
# Check memory usage
free -h
sudo supervisorctl restart halifax_api

# Monitor processes
top -p $(pgrep -d',' -f halifax)
```

#### 4. API Response Time Issues
```bash
# Check API performance
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# Monitor logs
tail -f /var/log/halifax_sentiment/api.log
```

### Log Analysis
```bash
# View recent errors
grep -i error /var/log/halifax_sentiment/api.log | tail -20

# Monitor real-time logs
sudo supervisorctl tail -f halifax_api

# Check system logs
sudo journalctl -u supervisor -f
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (HAProxy/Nginx)
- Deploy multiple API instances
- Use Redis for session storage
- Consider database read replicas

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Use caching strategies
- Implement connection pooling

## Maintenance

### Regular Maintenance Tasks
1. **Daily**: Check application logs and health
2. **Weekly**: Review performance metrics
3. **Monthly**: Update dependencies and security patches
4. **Quarterly**: Performance optimization review

### Update Procedure
```bash
# 1. Backup current state
./scripts/backup_db.sh
./scripts/backup_app.sh

# 2. Stop services
sudo supervisorctl stop halifax_api halifax_worker

# 3. Update code
git pull origin main
pip install -r requirements.txt

# 4. Run migrations
python -m alembic upgrade head

# 5. Restart services
sudo supervisorctl start halifax_api halifax_worker

# 6. Verify deployment
curl http://localhost:8000/health
```

## Support

For deployment support:
1. Check logs for error messages
2. Review configuration files
3. Test individual components
4. Contact development team with specific error details