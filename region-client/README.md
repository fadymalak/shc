# Region Client

Python script for deploying on servers in different regions to perform uptime checks from multiple geographic locations.

## Features

- Fetches monitors assigned to the region from the API
- Caches monitor configuration for 5 minutes (configurable)
- Performs checks based on monitor type (HTTP, DNS, Custom, TCP)
- Only reports incidents (downtime or high latency) to reduce API load
- Respects monitor check intervals
- Graceful shutdown handling

## Installation

1. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `API_BASE_URL`: Base URL of the uptime monitor API (e.g., `https://api.example.com`)
- `REGION_CODE`: Unique code for this region (must match region code in the dashboard)
- `API_KEY`: API key for authentication (from Region configuration)

Optional:
- `CACHE_TTL_MINUTES`: Cache TTL in minutes (default: 5)
- `CHECK_INTERVAL`: Base check interval in seconds (default: 60)

## Usage

### Run directly

```bash
python region_client.py
```

### Run as a service (systemd)

Create `/etc/systemd/system/region-client.service`:

```ini
[Unit]
Description=Uptime Monitor Region Client
After=network.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/opt/region-client
Environment="API_BASE_URL=https://api.example.com"
Environment="REGION_CODE=us-east-1"
Environment="API_KEY=your-api-key-here"
Environment="CACHE_TTL_MINUTES=5"
Environment="CHECK_INTERVAL=60"
ExecStart=/usr/bin/python3 /opt/region-client/region_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable region-client
sudo systemctl start region-client
sudo systemctl status region-client
```

### Run with Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY region_client.py .

CMD ["python", "region_client.py"]
```

Build and run:

```bash
docker build -t region-client .
docker run -d \
  --name region-client-us-east \
  -e API_BASE_URL=https://api.example.com \
  -e REGION_CODE=us-east-1 \
  -e API_KEY=your-api-key \
  region-client
```

### Run with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  region-client:
    build: .
    environment:
      - API_BASE_URL=${API_BASE_URL}
      - REGION_CODE=${REGION_CODE}
      - API_KEY=${API_KEY}
      - CACHE_TTL_MINUTES=5
      - CHECK_INTERVAL=60
    restart: unless-stopped
```

Run:

```bash
docker-compose up -d
```

## How It Works

1. **Initialization**: Client connects to API using region code and API key
2. **Monitor Fetching**: Fetches monitors assigned to this region
3. **Caching**: Caches monitor configuration for 5 minutes to reduce API calls
4. **Checking**: Performs checks based on each monitor's check interval
5. **Reporting**: Only submits results when incidents are detected (downtime or high latency)

## Monitor Types Supported

- **HTTP/HTTPS**: Checks web endpoints with status code validation
- **DNS**: Validates DNS records
- **Custom**: Checks for keywords in HTTP response
- **TCP**: Tests TCP connectivity

## Logging

The script logs to stdout with timestamps:
- Monitor cache refreshes
- Check results
- Errors

Redirect logs to a file:

```bash
python region_client.py >> /var/log/region-client.log 2>&1
```

## Troubleshooting

### Authentication errors
- Verify `API_KEY` matches the API key in the Region configuration
- Check that the region code exists in the dashboard

### No monitors found
- Ensure monitors are assigned to this region in the dashboard
- Check that monitors are active and not paused

### Connection errors
- Verify `API_BASE_URL` is correct and accessible
- Check network connectivity from the region server

### High CPU usage
- Increase `CHECK_INTERVAL` to reduce check frequency
- Reduce number of monitors assigned to this region
