# AWS EC2 Deployment Guide

This guide will walk you through deploying the Anime Roast Generator to AWS EC2 with Docker and Caddy.

## Prerequisites

- AWS EC2 instance (Ubuntu 22.04 LTS recommended)
- Domain pointing to your EC2 instance (anime-roast-generator.duckdns.org)
- SSH access to the server
- GitHub repository cloned on the server

## Server Setup

### 1. Connect to your EC2 instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. Update system packages

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 4. Clone your repository

```bash
cd ~
git clone https://github.com/oddava/anime-roast-generator.git
cd anime-roast-generator
```

### 5. Configure environment variables

```bash
# Copy the example file
cp .env.prod.example .env.prod

# Edit with your settings
nano .env.prod
```

Fill in your `GEMINI_API_KEY` and other settings.

### 6. Deploy the application

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 7. Setup auto-start on boot (Optional)

```bash
# Copy systemd service file
sudo cp anime-roast.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable anime-roast.service

# Start service
sudo systemctl start anime-roast.service

# Check status
sudo systemctl status anime-roast.service
```

## Updating the Application

To update to the latest version:

```bash
cd ~/anime-roast-generator
./deploy.sh
```

## Useful Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f caddy

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Check container status
docker-compose -f docker-compose.prod.yml ps

# View real-time stats
docker stats
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check for port conflicts
sudo netstat -tlnp | grep -E '(:80|:443)'
```

### SSL certificate issues

```bash
# Restart Caddy to trigger certificate renewal
docker-compose -f docker-compose.prod.yml restart caddy

# Check Caddy logs
docker-compose -f docker-compose.prod.yml logs caddy
```

### Backend not responding

```bash
# Check if backend is healthy
curl http://localhost:8000/health

# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend
```

## Security Considerations

1. **Firewall**: Ensure only ports 80, 443, and 22 are open
2. **Updates**: Regularly update the system and containers
3. **Secrets**: Never commit `.env.prod` to git
4. **Backups**: Regularly backup your data

## Architecture

```
Internet
    ↓
Caddy (Reverse Proxy + SSL)
    ↓
Docker Compose
    ├── Frontend (Nginx serving React)
    └── Backend (FastAPI + Uvicorn)
```

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Test locally: `docker-compose up`
- Review documentation in the repository

## SSL Certificates

Caddy automatically handles SSL certificates via Let's Encrypt. No manual configuration needed!

Your application should now be accessible at: https://anime-roast-generator.duckdns.org
