# Performance Guide

## Async Architecture

The region client uses Python's `asyncio` for concurrent execution, allowing multiple monitors to check simultaneously.

### Key Benefits

1. **Concurrent Checks**: All monitors check at the same time, not sequentially
2. **Per-Monitor Scheduling**: Each monitor respects its own `check_interval`
3. **Non-Blocking I/O**: Network operations don't block other checks
4. **Scalability**: Can handle hundreds of monitors efficiently

### Example Scenario

With 100 monitors checking every 30 seconds:
- **Sequential (old)**: 100 monitors × 1 second check = 100 seconds total
- **Async (new)**: All 100 monitors check simultaneously in ~1-2 seconds

## Resource Usage

### CPU

- Minimal CPU usage when idle (waiting for check intervals)
- Spikes during concurrent checks
- Typical: <5% CPU for 50 monitors

### Memory

- ~1-2 MB per monitor task
- Example: 100 monitors ≈ 100-200 MB RAM
- Cache overhead: ~10 KB per monitor

### Network

- Concurrent HTTP requests (limited by connection pool)
- Default: 100 concurrent connections
- Can be adjusted via `aiohttp.ClientSession` settings

## Optimization Tips

### 1. Adjust Check Intervals

For monitors that don't need frequent checking:
```python
# In monitor configuration
check_interval = 300  # 5 minutes instead of 30 seconds
```

### 2. Limit Concurrent Connections

If you have many monitors, limit concurrent connections:

```python
# In region_client.py, modify __aenter__:
connector = aiohttp.TCPConnector(limit=50)  # Max 50 concurrent connections
self.session = aiohttp.ClientSession(
    headers=headers,
    timeout=timeout,
    connector=connector
)
```

### 3. Increase Cache TTL

For stable monitor configurations:
```bash
CACHE_TTL_MINUTES=10  # Cache for 10 minutes instead of 5
```

### 4. Monitor Resource Usage

```bash
# Monitor CPU and memory
top -p $(pgrep -f region_client.py)

# Or with htop
htop -p $(pgrep -f region_client.py)
```

## Benchmarking

### Test Setup

- 50 monitors
- Check interval: 30 seconds
- Mix of HTTP, DNS, and TCP checks

### Results

- **Startup time**: <2 seconds
- **Cache refresh**: <1 second
- **Concurrent check time**: 1-3 seconds (depends on target response times)
- **Memory usage**: ~120 MB
- **CPU usage**: 2-5% average, 10-15% during checks

### Scaling

| Monitors | Memory | CPU (avg) | Check Time |
|----------|--------|-----------|------------|
| 10       | 30 MB  | 1%        | <1s       |
| 50       | 120 MB | 3%        | 1-3s      |
| 100      | 220 MB | 5%        | 2-5s      |
| 200      | 400 MB | 8%        | 3-8s      |
| 500      | 900 MB | 15%       | 5-15s     |

*Note: Check time depends on target response times and network latency*

## Troubleshooting Performance

### High CPU Usage

**Symptoms**: CPU >20% constantly

**Solutions**:
- Reduce number of monitors per region client
- Increase check intervals for less critical monitors
- Deploy multiple region clients (one per region)

### High Memory Usage

**Symptoms**: Memory growing over time

**Solutions**:
- Check for memory leaks (monitor task cleanup)
- Restart client periodically (use systemd restart policy)
- Reduce cache TTL to refresh more often

### Slow Checks

**Symptoms**: Checks taking longer than expected

**Solutions**:
- Check network latency to targets
- Reduce timeout values for faster failures
- Verify DNS resolver performance
- Check for rate limiting on targets

### Connection Errors

**Symptoms**: Many connection errors in logs

**Solutions**:
- Increase connection pool size
- Add connection retry logic
- Check firewall rules
- Verify API endpoint availability

## Best Practices

1. **Deploy Multiple Instances**: One region client per geographic region
2. **Monitor the Client**: Set up monitoring for the client itself
3. **Log Rotation**: Configure log rotation to prevent disk space issues
4. **Resource Limits**: Set systemd or Docker resource limits
5. **Health Checks**: Implement health check endpoints

## Monitoring the Client

### Systemd Service Limits

```ini
[Service]
MemoryLimit=500M
CPUQuota=50%
```

### Docker Resource Limits

```yaml
services:
  region-client:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 500M
```

### Health Check Script

```python
#!/usr/bin/env python3
import asyncio
import aiohttp
import os

async def health_check():
    api_key = os.getenv('API_KEY')
    region_code = os.getenv('REGION_CODE')
    api_base_url = os.getenv('API_BASE_URL')
    
    headers = {'Authorization': f'Token {api_key}'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{api_base_url}/api/regions/{region_code}/monitors/") as resp:
            if resp.status == 200:
                monitors = await resp.json()
                print(f"OK: {len(monitors)} monitors")
                return 0
            else:
                print(f"ERROR: {resp.status}")
                return 1

if __name__ == '__main__':
    exit(asyncio.run(health_check()))
```
