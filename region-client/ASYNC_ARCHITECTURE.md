# Async Architecture Overview

## Why Async?

The region client was refactored to use Python's `asyncio` to support:
- **Concurrent checking** of multiple monitors
- **Per-monitor scheduling** where each monitor checks at its own interval (e.g., every 30 seconds)
- **High performance** with hundreds of monitors running simultaneously
- **Non-blocking I/O** for network operations

## Architecture

### Before (Synchronous)

```
Main Loop
  ├─ Check Monitor 1 (wait for response)
  ├─ Check Monitor 2 (wait for response)
  ├─ Check Monitor 3 (wait for response)
  └─ ... (sequential, blocking)
```

**Problem**: With 100 monitors checking every 30 seconds, each check taking 1 second:
- Total time: 100 seconds
- Monitors checked sequentially
- Wasted time waiting for network I/O

### After (Async)

```
Main Loop (async)
  ├─ Task 1: Monitor 1 loop (checks every 30s)
  ├─ Task 2: Monitor 2 loop (checks every 30s)
  ├─ Task 3: Monitor 3 loop (checks every 30s)
  └─ ... (all running concurrently)
```

**Solution**: All monitors check simultaneously:
- Total time: ~1-2 seconds (depends on slowest check)
- Monitors checked concurrently
- Network I/O doesn't block other checks

## Key Components

### 1. MonitorCache (Async)

```python
class MonitorCache:
    async def is_expired() -> bool
    async def get_monitors() -> Dict[int, MonitorConfig]
    async def update(monitors: List[MonitorConfig])
```

- Thread-safe async cache
- Uses `asyncio.Lock` for synchronization
- Caches monitor configuration for 5 minutes

### 2. RegionClient (Async Context Manager)

```python
async with RegionClient(...) as client:
    await client.run()
```

- Manages `aiohttp.ClientSession` lifecycle
- Initializes DNS resolver
- Cleans up resources on exit

### 3. Monitor Tasks

Each monitor gets its own async task:

```python
async def monitor_loop(monitor: MonitorConfig):
    while running:
        result = await perform_check(monitor)
        if result.incident_type:
            await submit_result(result)
        await asyncio.sleep(monitor.check_interval)
```

- Independent scheduling per monitor
- Respects individual `check_interval`
- Runs concurrently with other monitors

### 4. Check Methods (Async)

All check methods are async:

- `check_http()` - Uses `aiohttp` for async HTTP requests
- `check_dns()` - Uses `aiodns` for async DNS queries
- `check_custom()` - Async HTTP with content checking
- `check_tcp()` - Async TCP connection using `asyncio.open_connection()`

## Example Flow

### Startup

```
1. Initialize RegionClient
2. Create aiohttp session
3. Fetch monitors from API
4. Create async task for each monitor
5. Start cache refresh background task
6. All tasks run concurrently
```

### Runtime

```
Monitor 1 Task: Check → Wait 30s → Check → Wait 30s → ...
Monitor 2 Task: Check → Wait 60s → Check → Wait 60s → ...
Monitor 3 Task: Check → Wait 30s → Check → Wait 30s → ...
Cache Refresh: Wait 5min → Refresh → Wait 5min → ...
```

All tasks run **simultaneously** without blocking each other.

## Benefits

### 1. Performance

- **Before**: 100 monitors × 1s = 100 seconds
- **After**: 100 monitors concurrently = ~1-2 seconds

### 2. Scalability

- Can handle hundreds of monitors
- Resource usage scales linearly
- No blocking I/O operations

### 3. Flexibility

- Each monitor has its own schedule
- Easy to add/remove monitors dynamically
- Independent error handling per monitor

### 4. Efficiency

- Non-blocking network operations
- Better CPU utilization
- Lower latency for incident detection

## Resource Management

### Connection Pooling

`aiohttp.ClientSession` manages connection pooling:
- Reuses connections for better performance
- Limits concurrent connections (default: 100)
- Handles connection lifecycle automatically

### Task Management

```python
# Create task
task = asyncio.create_task(monitor_loop(monitor))

# Cancel task
task.cancel()
await task  # Wait for cancellation
```

- Tasks are created/destroyed dynamically
- Proper cleanup on monitor removal
- Graceful shutdown handling

## Error Handling

Each monitor task handles errors independently:

```python
try:
    result = await perform_check(monitor)
except Exception as e:
    # Log error, wait 5s, retry
    await asyncio.sleep(5)
```

- Errors in one monitor don't affect others
- Automatic retry with backoff
- Proper error logging

## Monitoring

### Task Count

```python
len(client.monitor_tasks)  # Number of active monitor tasks
```

### Check Times

```python
client.last_check_time  # Dict of last check time per monitor
```

### Resource Usage

Monitor with standard tools:
- `top` / `htop` for CPU/memory
- `netstat` for network connections
- Logs for check frequency

## Best Practices

1. **Monitor Count**: Keep <500 monitors per region client
2. **Check Intervals**: Use appropriate intervals (30s-5min)
3. **Resource Limits**: Set systemd/Docker limits
4. **Monitoring**: Monitor the client itself
5. **Logging**: Use structured logging for better insights

## Troubleshooting

### High CPU

- Reduce monitor count per client
- Increase check intervals
- Check for tight loops

### High Memory

- Monitor task cleanup
- Check for memory leaks
- Restart periodically

### Slow Checks

- Check network latency
- Verify DNS resolver
- Check connection pool limits

## Future Enhancements

Potential improvements:
- Connection pool size configuration
- Retry logic with exponential backoff
- Metrics collection (Prometheus)
- Health check endpoint
- Graceful degradation
