# EZ-Trip Production Deployment Guide

This guide provides step-by-step instructions for deploying EZ-Trip to a production environment.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended) or cloud platform (AWS, GCP, Azure, DigitalOcean)
- Docker and Docker Compose installed
- Domain name (optional but recommended)
- SSL/TLS certificate (Let's Encrypt recommended)

## Server Requirements

### Minimum Requirements
- 2 CPU cores
- 4GB RAM
- 20GB storage

### Recommended for Production
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ SSD storage
- Dedicated database server (or MongoDB Atlas)

## Step 1: Server Setup

### 1.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 1.3 Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Log out and back in for group changes to take effect.

## Step 2: Clone Repository

```bash
git clone https://github.com/yourusername/EZ-Trip.git
cd EZ-Trip
```

## Step 3: Environment Configuration

### 3.1 Create Production Environment File

```bash
cp .env.production.template .env
```

### 3.2 Configure Environment Variables

Edit the `.env` file with your production values:

```bash
nano .env
```

**Critical variables to configure:**

```env
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# OpenAI API
OPENAI_API_KEY=sk-proj-your_actual_production_key_here

# Google OAuth (create separate production credentials)
GOOGLE_CLIENT_ID=your_production_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_production_client_secret

# Database
MONGODB_URI=mongodb://mongodb:27017/
DB_NAME=production_database

# Email (use production email service)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USERNAME=production_email@domain.com
SMTP_PASSWORD=your_app_specific_password
EMAIL_FROM_ADDRESS=EZ Trip <noreply@yourdomain.com>
EMAIL_FROM_NAME=EZ Trip

# Security - Generate random secrets
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
SESSION_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# CORS - Your actual production domains
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Frontend
REACT_APP_BACKEND_URL=https://api.yourdomain.com
REACT_APP_GOOGLE_CLIENT_ID=your_production_client_id.apps.googleusercontent.com
```

### 3.3 Set File Permissions

```bash
chmod 600 .env
```

## Step 4: Google OAuth Configuration

1. Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `https://yourdomain.com`
   - `https://www.yourdomain.com`
6. Copy Client ID and Client Secret to `.env`

## Step 5: SSL/TLS Setup (Recommended)

### Option A: Using Let's Encrypt with Nginx Reverse Proxy

1. **Install Certbot:**

```bash
sudo apt install certbot python3-certbot-nginx -y
```

2. **Create Nginx configuration** for reverse proxy:

```bash
sudo nano /etc/nginx/sites-available/eztrip
```

```nginx
server {
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Enable site and get certificate:**

```bash
sudo ln -s /etc/nginx/sites-available/eztrip /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Option B: Using Cloudflare (Free SSL)

1. Add your domain to Cloudflare
2. Update nameservers at your domain registrar
3. Enable "Full (strict)" SSL mode
4. Cloudflare will handle SSL automatically

## Step 6: Build and Deploy

### 6.1 Build Production Images

```bash
docker-compose -f docker-compose.prod.yml build
```

### 6.2 Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 6.3 Verify Deployment

```bash
# Check running containers
docker ps

# Check backend logs
docker logs eztrip-backend-prod

# Check frontend logs
docker logs eztrip-frontend-prod

# Check MongoDB logs
docker logs eztrip-mongodb-prod
```

### 6.4 Test Application

Visit your domain and test:
- Frontend loads correctly
- User registration works
- Google OAuth login works
- Trip creation and expense tracking
- Email notifications (check spam folder)

## Step 7: MongoDB Security (Recommended)

### 7.1 Enable Authentication

1. **Create MongoDB admin user:**

```bash
docker exec -it eztrip-mongodb-prod mongosh

use admin
db.createUser({
  user: "admin",
  pwd: "strong_password_here",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
})

use production_database
db.createUser({
  user: "eztrip_user",
  pwd: "another_strong_password",
  roles: [ { role: "readWrite", db: "production_database" } ]
})

exit
```

2. **Update docker-compose.prod.yml:**

```yaml
mongodb:
  environment:
    MONGO_INITDB_ROOT_USERNAME: admin
    MONGO_INITDB_ROOT_PASSWORD: strong_password_here
```

3. **Update `.env`:**

```env
MONGO_URL=mongodb://eztrip_user:another_strong_password@mongodb:27017/production_database?authSource=production_database
```

4. **Restart services:**

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## Step 8: Backup Strategy

### 8.1 MongoDB Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/eztrip"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup MongoDB
docker exec eztrip-mongodb-prod mongodump --out=/data/backup/$DATE

# Copy backup from container
docker cp eztrip-mongodb-prod:/data/backup/$DATE $BACKUP_DIR/

# Keep only last 7 days of backups
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

### 8.2 Setup Cron Job

```bash
chmod +x backup.sh
crontab -e
```

Add line:
```
0 2 * * * /path/to/backup.sh >> /var/log/eztrip-backup.log 2>&1
```

## Step 9: Monitoring & Maintenance

### 9.1 Log Monitoring

```bash
# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker logs -f eztrip-backend-prod
```

### 9.2 Resource Monitoring

```bash
# Docker stats
docker stats

# Server resources
htop
```

### 9.3 Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up --build -d

# Remove old images
docker image prune -a
```

## Step 10: Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## Troubleshooting

### Backend not starting

```bash
docker logs eztrip-backend-prod
```

Common issues:
- Missing environment variables
- Invalid API keys
- Database connection issues

### Frontend not loading

```bash
docker logs eztrip-frontend-prod
```

Common issues:
- Incorrect `REACT_APP_BACKEND_URL`
- CORS configuration mismatch
- Build errors

### Database connection errors

- Check MongoDB is running: `docker ps`
- Verify connection string in `.env`
- Check MongoDB logs: `docker logs eztrip-mongodb-prod`

## Performance Optimization

### 1. Database Indexing

```javascript
// Connect to MongoDB
mongosh mongodb://localhost:27017/production_database

// Create indexes for better performance
db.users.createIndex({ email: 1 }, { unique: true })
db.trips.createIndex({ created_by: 1 })
db.expenses.createIndex({ trip_id: 1 })
db.user_sessions.createIndex({ session_token: 1 }, { unique: true })
db.user_sessions.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })
```

### 2. Enable Compression

Already configured in `nginx.conf` for frontend.

### 3. Use CDN

Consider using Cloudflare or another CDN for static assets.

## Security Checklist

- [ ] SSL/TLS certificate installed and working
- [ ] Environment variables properly configured
- [ ] MongoDB authentication enabled
- [ ] Firewall configured
- [ ] Strong passwords for all services
- [ ] 2FA enabled on external accounts
- [ ] Regular backups configured
- [ ] Monitoring and logging enabled
- [ ] CORS properly restricted
- [ ] Security headers enabled
- [ ] Docker containers running as non-root
- [ ] API keys rotated (different from development)

## Support

For issues or questions:
- Check logs first
- Review [SECURITY.md](SECURITY.md) for security-related issues
- Open an issue on GitHub
- Contact support team

## Scaling Recommendations

For high-traffic scenarios:

1. **Use managed database** (MongoDB Atlas)
2. **Separate frontend/backend servers**
3. **Add load balancer** (nginx, HAProxy)
4. **Use Redis for sessions**
5. **Implement caching** (Redis, Memcached)
6. **Use CDN** for static assets
7. **Horizontal scaling** with Docker Swarm or Kubernetes
