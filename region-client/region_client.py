#!/usr/bin/env python3
"""
Region Client for Uptime Monitor (Async Version)
Deploy this script on servers in different regions to perform checks from multiple locations.
Uses async/await for concurrent monitor checking.
"""

import os
import sys
import asyncio
import signal
import socket
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from asyncio import Lock
import aiohttp
import aiodns
from decouple import config


@dataclass
class MonitorConfig:
    """Monitor configuration"""
    id: int
    name: str
    check_type: str
    target: str
    expected_status_code: Optional[int]
    expected_keyword: Optional[str]
    expected_dns_record: Optional[str]
    dns_record_type: Optional[str]
    timeout: int
    high_latency_threshold: int
    check_interval: int


@dataclass
class CheckResult:
    """Result of a monitor check"""
    monitor_id: int
    status: str  # 'up', 'down', 'high_latency'
    response_time_ms: Optional[int]
    status_code: Optional[int]
    error_message: Optional[str]
    incident_type: Optional[str]  # 'downtime' or 'high_latency'


class MonitorCache:
    """Cache for monitor configurations"""
    
    def __init__(self, cache_ttl_minutes: int = 5):
        self.cache_ttl_minutes = cache_ttl_minutes
        self.monitors: Dict[int, MonitorConfig] = {}
        self.last_fetch: Optional[datetime] = None
        self.lock = Lock()
    
    async def is_expired(self) -> bool:
        """Check if cache has expired"""
        async with self.lock:
            if self.last_fetch is None:
                return True
            return datetime.now() - self.last_fetch > timedelta(minutes=self.cache_ttl_minutes)
    
    async def get_monitors(self) -> Dict[int, MonitorConfig]:
        """Get cached monitors"""
        async with self.lock:
            return self.monitors.copy()
    
    async def update(self, monitors: List[MonitorConfig]):
        """Update cache with new monitors"""
        async with self.lock:
            self.monitors = {m.id: m for m in monitors}
            self.last_fetch = datetime.now()
    
    async def clear(self):
        """Clear cache"""
        async with self.lock:
            self.monitors = {}
            self.last_fetch = None


class RegionClient:
    """Async client for performing checks from a specific region"""
    
    def __init__(self, api_base_url: str, region_code: str, api_key: str, cache_ttl_minutes: int = 5):
        self.api_base_url = api_base_url.rstrip('/')
        self.region_code = region_code
        self.api_key = api_key
        self.cache = MonitorCache(cache_ttl_minutes)
        self.running = True
        self.session: Optional[aiohttp.ClientSession] = None
        self.dns_resolver: Optional[aiodns.DNSResolver] = None
        self.monitor_tasks: Dict[int, asyncio.Task] = {}
        self.last_check_time: Dict[int, float] = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'application/json',
        }
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        self.dns_resolver = aiodns.DNSResolver()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_monitors(self) -> List[MonitorConfig]:
        """Fetch monitors assigned to this region"""
        try:
            url = f"{self.api_base_url}/api/regions/{self.region_code}/monitors/"
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Handle both list and dict responses
                if isinstance(data, dict) and 'results' in data:
                    monitors_data = data['results']
                elif isinstance(data, list):
                    monitors_data = data
                else:
                    monitors_data = [data] if data else []
                
                monitors = []
                for monitor_data in monitors_data:
                    monitor = MonitorConfig(
                        id=monitor_data['id'],
                        name=monitor_data['name'],
                        check_type=monitor_data['check_type'],
                        target=monitor_data['target'],
                        expected_status_code=monitor_data.get('expected_status_code'),
                        expected_keyword=monitor_data.get('expected_keyword'),
                        expected_dns_record=monitor_data.get('expected_dns_record'),
                        dns_record_type=monitor_data.get('dns_record_type', 'A'),
                        timeout=monitor_data.get('timeout', 30),
                        high_latency_threshold=monitor_data.get('high_latency_threshold', 5000),
                        check_interval=monitor_data.get('check_interval', 60),
                    )
                    monitors.append(monitor)
                
                return monitors
        except Exception as e:
            print(f"[{datetime.now()}] Error fetching monitors: {e}", file=sys.stderr)
            return []
    
    async def check_http(self, monitor: MonitorConfig) -> CheckResult:
        """Perform HTTP/HTTPS check"""
        start_time = asyncio.get_event_loop().time()
        try:
            timeout = aiohttp.ClientTimeout(total=monitor.timeout)
            async with self.session.get(
                monitor.target,
                allow_redirects=True,
                ssl=True,
                timeout=timeout
            ) as response:
                response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                status_code = response.status
                
                status = 'up'
                incident_type = None
                
                # Check expected status code
                if monitor.expected_status_code and status_code != monitor.expected_status_code:
                    status = 'down'
                    incident_type = 'downtime'
                    error_message = f"Expected status {monitor.expected_status_code}, got {status_code}"
                else:
                    error_message = None
                
                # Check for high latency
                if response_time_ms > monitor.high_latency_threshold:
                    if status == 'up':
                        status = 'high_latency'
                        incident_type = 'high_latency'
                
                return CheckResult(
                    monitor_id=monitor.id,
                    status=status,
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    error_message=error_message,
                    incident_type=incident_type,
                )
        except Exception as e:
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    async def check_dns(self, monitor: MonitorConfig) -> CheckResult:
        """Perform DNS check"""
        start_time = asyncio.get_event_loop().time()
        try:
            record_type = monitor.dns_record_type or 'A'
            
            # Convert DNS record type string to aiodns constant
            dns_type_map = {
                'A': aiodns.DNS_TYPE_A,
                'AAAA': aiodns.DNS_TYPE_AAAA,
                'MX': aiodns.DNS_TYPE_MX,
                'TXT': aiodns.DNS_TYPE_TXT,
                'CNAME': aiodns.DNS_TYPE_CNAME,
            }
            dns_type = dns_type_map.get(record_type.upper(), aiodns.DNS_TYPE_A)
            
            answers = await asyncio.wait_for(
                self.dns_resolver.query(monitor.target, dns_type),
                timeout=monitor.timeout
            )
            
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            status = 'up'
            error_message = None
            
            # Check expected DNS record
            if monitor.expected_dns_record:
                found = False
                for answer in answers:
                    if hasattr(answer, 'host') and str(answer.host) == monitor.expected_dns_record:
                        found = True
                        break
                    elif str(answer) == monitor.expected_dns_record:
                        found = True
                        break
                if not found:
                    status = 'down'
                    error_message = f"Expected DNS record {monitor.expected_dns_record} not found"
            
            incident_type = None
            if response_time_ms > monitor.high_latency_threshold:
                status = 'high_latency'
                incident_type = 'high_latency'
            
            return CheckResult(
                monitor_id=monitor.id,
                status=status,
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=error_message,
                incident_type=incident_type,
            )
        except asyncio.TimeoutError:
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message="DNS query timeout",
                incident_type='downtime',
            )
        except Exception as e:
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    async def check_custom(self, monitor: MonitorConfig) -> CheckResult:
        """Perform custom keyword check"""
        start_time = asyncio.get_event_loop().time()
        try:
            timeout = aiohttp.ClientTimeout(total=monitor.timeout)
            async with self.session.get(
                monitor.target,
                allow_redirects=True,
                timeout=timeout
            ) as response:
                response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                text = await response.text()
                status_code = response.status
                
                status = 'up'
                error_message = None
                
                # Check for expected keyword
                if monitor.expected_keyword:
                    if monitor.expected_keyword.lower() not in text.lower():
                        status = 'down'
                        error_message = f"Expected keyword '{monitor.expected_keyword}' not found in response"
                
                incident_type = None
                if response_time_ms > monitor.high_latency_threshold:
                    if status == 'up':
                        status = 'high_latency'
                        incident_type = 'high_latency'
                
                return CheckResult(
                    monitor_id=monitor.id,
                    status=status,
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    error_message=error_message,
                    incident_type=incident_type,
                )
        except Exception as e:
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    async def check_tcp(self, monitor: MonitorConfig) -> CheckResult:
        """Perform TCP check"""
        start_time = asyncio.get_event_loop().time()
        try:
            # Parse host and port
            if ':' in monitor.target:
                host, port = monitor.target.split(':')
                port = int(port)
            else:
                host = monitor.target
                port = 80
            
            # Use asyncio for TCP connection
            result_code = 0
            error_msg = None
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=monitor.timeout
                )
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                result_code = 1
                error_msg = str(e)
            
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            status = 'up' if result_code == 0 else 'down'
            error_message = None if result_code == 0 else (error_msg or "TCP connection failed")
            
            incident_type = None
            if status == 'down':
                incident_type = 'downtime'
            elif response_time_ms > monitor.high_latency_threshold:
                status = 'high_latency'
                incident_type = 'high_latency'
            
            return CheckResult(
                monitor_id=monitor.id,
                status=status,
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=error_message,
                incident_type=incident_type,
            )
        except asyncio.TimeoutError:
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message="TCP connection timeout",
                incident_type='downtime',
            )
        except Exception as e:
            response_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    async def perform_check(self, monitor: MonitorConfig) -> CheckResult:
        """Perform check based on monitor type"""
        if monitor.check_type in ['http', 'https']:
            return await self.check_http(monitor)
        elif monitor.check_type == 'dns':
            return await self.check_dns(monitor)
        elif monitor.check_type == 'custom':
            return await self.check_custom(monitor)
        elif monitor.check_type == 'tcp':
            return await self.check_tcp(monitor)
        else:
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=None,
                status_code=None,
                error_message=f"Unknown check type: {monitor.check_type}",
                incident_type='downtime',
            )
    
    async def submit_result(self, result: CheckResult):
        """Submit check result to API"""
        try:
            url = f"{self.api_base_url}/api/regions/{self.region_code}/check-results/"
            data = {
                'monitor_id': result.monitor_id,
                'status': result.status,
                'response_time_ms': result.response_time_ms,
                'status_code': result.status_code,
                'error_message': result.error_message,
                'incident_type': result.incident_type,
            }
            async with self.session.post(url, json=data) as response:
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"[{datetime.now()}] Error submitting result for monitor {result.monitor_id}: {e}", file=sys.stderr)
            return False
    
    async def refresh_monitors(self):
        """Refresh monitor cache if expired"""
        if await self.cache.is_expired():
            print(f"[{datetime.now()}] Refreshing monitor cache...")
            monitors = await self.fetch_monitors()
            if monitors:
                await self.cache.update(monitors)
                print(f"[{datetime.now()}] Loaded {len(monitors)} monitors")
                
                # Update monitor tasks
                await self.update_monitor_tasks(monitors)
            else:
                print(f"[{datetime.now()}] No monitors found or error occurred")
    
    async def update_monitor_tasks(self, monitors: List[MonitorConfig]):
        """Update monitor tasks - start new ones, cancel removed ones"""
        current_monitor_ids = {m.id for m in monitors}
        
        # Cancel tasks for monitors that no longer exist
        for monitor_id in list(self.monitor_tasks.keys()):
            if monitor_id not in current_monitor_ids:
                task = self.monitor_tasks.pop(monitor_id)
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        
        # Start tasks for new monitors or restart done ones
        monitors_dict = {m.id: m for m in monitors}
        for monitor_id, monitor in monitors_dict.items():
            if monitor_id not in self.monitor_tasks or self.monitor_tasks[monitor_id].done():
                if monitor_id in self.monitor_tasks:
                    # Remove done task
                    self.monitor_tasks.pop(monitor_id)
                # Create new task
                self.monitor_tasks[monitor_id] = asyncio.create_task(
                    self.monitor_loop(monitor)
                )
    
    async def monitor_loop(self, monitor: MonitorConfig):
        """Individual monitor check loop - runs continuously for each monitor"""
        while self.running:
            try:
                # Perform check
                result = await self.perform_check(monitor)
                self.last_check_time[monitor.id] = asyncio.get_event_loop().time()
                
                # Only submit if there's an incident
                if result.incident_type:
                    await self.submit_result(result)
                    print(f"[{datetime.now()}] Monitor {monitor.name}: {result.status} "
                          f"({result.response_time_ms}ms) - {result.incident_type}")
                else:
                    print(f"[{datetime.now()}] Monitor {monitor.name}: {result.status} "
                          f"({result.response_time_ms}ms)")
                
                # Wait for next check interval
                await asyncio.sleep(monitor.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[{datetime.now()}] Error in monitor loop for {monitor.name}: {e}", file=sys.stderr)
                # Wait a bit before retrying
                await asyncio.sleep(5)
    
    async def cache_refresh_loop(self):
        """Background task to refresh monitor cache periodically"""
        while self.running:
            try:
                await self.refresh_monitors()
                # Refresh cache every cache TTL minutes
                await asyncio.sleep(self.cache.cache_ttl_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[{datetime.now()}] Error in cache refresh loop: {e}", file=sys.stderr)
                await asyncio.sleep(60)  # Retry in 1 minute
    
    async def run(self):
        """Main async run loop"""
        print(f"[{datetime.now()}] Starting async region client for region: {self.region_code}")
        print(f"[{datetime.now()}] API URL: {self.api_base_url}")
        print(f"[{datetime.now()}] Cache TTL: {self.cache.cache_ttl_minutes} minutes")
        
        # Initial monitor fetch
        await self.refresh_monitors()
        
        # Start cache refresh task
        cache_task = asyncio.create_task(self.cache_refresh_loop())
        
        try:
            # Wait for all monitor tasks
            if self.monitor_tasks:
                await asyncio.gather(*self.monitor_tasks.values(), return_exceptions=True)
            else:
                # If no monitors, just wait
                while self.running:
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Shutting down...")
            self.running = False
        finally:
            # Cancel cache refresh task
            cache_task.cancel()
            try:
                await cache_task
            except asyncio.CancelledError:
                pass
            
            # Cancel all monitor tasks
            for task in self.monitor_tasks.values():
                task.cancel()
            if self.monitor_tasks:
                await asyncio.gather(*self.monitor_tasks.values(), return_exceptions=True)


async def main_async():
    """Main async entry point"""
    # Configuration from environment variables
    api_base_url = config('API_BASE_URL', default='http://localhost:8000')
    region_code = config('REGION_CODE', default='')
    api_key = config('API_KEY', default='')
    cache_ttl_minutes = config('CACHE_TTL_MINUTES', default=5, cast=int)
    
    if not region_code:
        print("Error: REGION_CODE environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    if not api_key:
        print("Error: API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    # Create and run client
    client = RegionClient(api_base_url, region_code, api_key, cache_ttl_minutes)
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print(f"\n[{datetime.now()}] Received shutdown signal")
        client.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        async with client:
            await client.run()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Shutting down...")
        sys.exit(0)


if __name__ == '__main__':
    main()
