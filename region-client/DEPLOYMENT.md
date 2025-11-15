# Region Client Deployment Guide

This guide explains how to deploy the region client script on servers in different regions.

## Overview

The region client is a lightweight **async Python script** that:
- Fetches monitors assigned to its region from the API
- Caches monitor configuration for 5 minutes
- Runs each monitor in its own async task for concurrent checking
- Performs checks based on each monitor's individual check interval (e.g., every 30 seconds)
- Only reports incidents (downtime or high latency) to reduce API load
- Can handle hundreds of monitors simultaneously

## Prerequisites

1. **Create a Region in the Dashboard**
   - Go to Regions in the dashboard
   - Create a new region with:
     - Name: e.g., "US East"
     - Code: e.g., "us-east-1" (must be unique)
     - Location: e.g., "Virginia, USA"
     - Client Endpoint: URL where client will be deployed (optional)
     - API Key: Generate a secure API key (save this!)

2. **Assign Monitors to Region**
   - Go to Monitors
   - Edit monitors and assign them to the region(s) you want to check from

## Deployment Options

### Option 1: Direct Python Installation

1. **Install Python 3.11+**

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

2. **Clone or copy the region-client directory**

```bash
cd /opt
sudo mkdir region-client
sudo chown $USER:$USER region-client
cd region-client
# Copy region_client.py and requirements.txt here
```

3. **Create virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp .env.example .env
nano .env
```

Set:
- `API_BASE_URL`: Your API URL (e.g., `https://api.example.com`)
- `REGION_CODE`: The region code you created (e.g., `us-east-1`)
- `API_KEY`: The API key from the region configuration

5. **Test run**

```bash
python region_client.py
```

6. **Set up as systemd service**

```bash
sudo cp systemd.service.example /etc/systemd/system/region-client.service
sudo nano /etc/systemd/system/region-client.service
# Update paths and environment variables

sudo systemctl daemon-reload
sudo systemctl enable region-client
sudo systemctl start region-client
sudo systemctl status region-client
```

### Option 2: Docker Deployment

1. **Build the image**

```bash
cd region-client
docker build -t region-client:latest .
```

2. **Run the container**

```bash
docker run -d \
  --name region-client-us-east \
  --restart unless-stopped \
  -e API_BASE_URL=https://api.example.com \
  -e REGION_CODE=us-east-1 \
  -e API_KEY=your-api-key-here \
  -e CACHE_TTL_MINUTES=5 \
  -e CHECK_INTERVAL=60 \
  region-client:latest
```

3. **View logs**

```bash
docker logs -f region-client-us-east
```

### Option 3: Docker Compose (Multiple Regions)

1. **Create docker-compose.yml**

```bash
cp docker-compose.example.yml docker-compose.yml
nano docker-compose.yml
```

2. **Set environment variables**

Create `.env` file:
```
API_KEY_US_EAST=your-us-east-api-key
API_KEY_EU_WEST=your-eu-west-api-key
```

3. **Start services**

```bash
docker-compose up -d
```

4. **View logs**

```bash
docker-compose logs -f
```

## Verification

1. **Check logs**

```bash
# Systemd
sudo journalctl -u region-client -f

# Docker
docker logs -f region-client-us-east
```

You should see:
```
[2024-01-01 12:00:00] Starting region client for region: us-east-1
[2024-01-01 12:00:01] Refreshing monitor cache...
[2024-01-01 12:00:02] Loaded 5 monitors
[2024-01-01 12:00:03] Monitor Example Monitor: up (234ms)
```

2. **Check API**

Monitor incidents should appear in the dashboard when issues are detected.

## Troubleshooting

### Authentication Errors

**Error**: `Invalid API key`

**Solution**:
- Verify the API key matches the one in the Region configuration
- Ensure the region is active in the dashboard
- Check that the API key is correctly set in environment variables

### No Monitors Found

**Error**: `No monitors to check`

**Solution**:
- Ensure monitors are assigned to this region in the dashboard
- Verify monitors are active and not paused
- Check that the region code matches exactly (case-sensitive)

### Connection Errors

**Error**: `Error fetching monitors: Connection refused`

**Solution**:
- Verify `API_BASE_URL` is correct and accessible
- Check network connectivity from the server
- Ensure firewall allows outbound HTTPS connections
- Verify SSL certificate is valid if using HTTPS

### High Resource Usage

**Symptoms**: High CPU or memory usage

**Solution**:
- Increase `CHECK_INTERVAL` to reduce check frequency
- Reduce number of monitors assigned to this region
- Increase `CACHE_TTL_MINUTES` to reduce API calls

## Monitoring the Client

### Health Check Endpoint

You can create a simple health check script:

```python
#!/usr/bin/env python3
import requests
import sys

api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv('API_KEY')
region_code = sys.argv[2] if len(sys.argv) > 2 else os.getenv('REGION_CODE')

response = requests.get(
    f"{os.getenv('API_BASE_URL')}/api/regions/{region_code}/monitors/",
    headers={'Authorization': f'Token {api_key}'}
)

if response.status_code == 200:
    monitors = response.json()
    print(f"OK: {len(monitors)} monitors configured")
    sys.exit(0)
else:
    print(f"ERROR: {response.status_code}")
    sys.exit(1)
```

### Log Rotation

For systemd, configure log rotation in `/etc/logrotate.d/region-client`:

```
/var/log/region-client.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 monitor monitor
}
```

## Security Considerations

1. **API Key Security**
   - Store API keys securely (use environment variables, not files)
   - Rotate API keys periodically
   - Use different API keys for each region

2. **Network Security**
   - Use HTTPS for API communication
   - Consider VPN or private network for API access
   - Restrict outbound connections if possible

3. **Server Security**
   - Run client as non-root user
   - Keep Python and dependencies updated
   - Use firewall rules to restrict access

## Scaling

To handle more monitors:

1. **Deploy multiple instances** of the client (with different region codes)
2. **Increase check interval** for less critical monitors
3. **Use load balancing** if deploying multiple instances of the same region
4. **Monitor resource usage** and scale accordingly

## Best Practices

1. **Region Naming**: Use consistent naming (e.g., `us-east-1`, `eu-west-1`)
2. **Monitoring**: Set up monitoring for the client itself (process monitoring, log monitoring)
3. **Updates**: Keep the client script updated
4. **Documentation**: Document which servers run which regions
5. **Backup**: Keep configuration backed up
