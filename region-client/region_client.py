#!/usr/bin/env python3
"""
Region Client for Uptime Monitor
Deploy this script on servers in different regions to perform checks from multiple locations.
"""

import os
import sys
import time
import json
import socket
import ssl
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from threading import Lock
import requests
import dns.resolver
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
    
    def is_expired(self) -> bool:
        """Check if cache has expired"""
        if self.last_fetch is None:
            return True
        return datetime.now() - self.last_fetch > timedelta(minutes=self.cache_ttl_minutes)
    
    def get_monitors(self) -> Dict[int, MonitorConfig]:
        """Get cached monitors"""
        with self.lock:
            return self.monitors.copy()
    
    def update(self, monitors: List[MonitorConfig]):
        """Update cache with new monitors"""
        with self.lock:
            self.monitors = {m.id: m for m in monitors}
            self.last_fetch = datetime.now()
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.monitors = {}
            self.last_fetch = None


class RegionClient:
    """Client for performing checks from a specific region"""
    
    def __init__(self, api_base_url: str, region_code: str, api_key: str, cache_ttl_minutes: int = 5):
        self.api_base_url = api_base_url.rstrip('/')
        self.region_code = region_code
        self.api_key = api_key
        self.cache = MonitorCache(cache_ttl_minutes)
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json',
        })
        self.running = True
    
    def fetch_monitors(self) -> List[MonitorConfig]:
        """Fetch monitors assigned to this region"""
        try:
            url = f"{self.api_base_url}/api/regions/{self.region_code}/monitors/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Handle both list and dict responses
            data = response.json()
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
            print(f"Error fetching monitors: {e}", file=sys.stderr)
            return []
    
    def check_http(self, monitor: MonitorConfig) -> CheckResult:
        """Perform HTTP/HTTPS check"""
        start_time = time.time()
        try:
            response = requests.get(
                monitor.target,
                timeout=monitor.timeout,
                allow_redirects=True,
                verify=True
            )
            response_time_ms = int((time.time() - start_time) * 1000)
            
            status = 'up'
            incident_type = None
            
            # Check expected status code
            if monitor.expected_status_code and response.status_code != monitor.expected_status_code:
                status = 'down'
                incident_type = 'downtime'
                error_message = f"Expected status {monitor.expected_status_code}, got {response.status_code}"
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
                status_code=response.status_code,
                error_message=error_message,
                incident_type=incident_type,
            )
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    def check_dns(self, monitor: MonitorConfig) -> CheckResult:
        """Perform DNS check"""
        start_time = time.time()
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = monitor.timeout
            resolver.lifetime = monitor.timeout
            
            record_type = monitor.dns_record_type or 'A'
            answers = resolver.resolve(monitor.target, record_type)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            status = 'up'
            error_message = None
            
            # Check expected DNS record
            if monitor.expected_dns_record:
                found = False
                for answer in answers:
                    if str(answer) == monitor.expected_dns_record:
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
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    def check_custom(self, monitor: MonitorConfig) -> CheckResult:
        """Perform custom keyword check"""
        start_time = time.time()
        try:
            response = requests.get(
                monitor.target,
                timeout=monitor.timeout,
                allow_redirects=True
            )
            response_time_ms = int((time.time() - start_time) * 1000)
            
            status = 'up'
            error_message = None
            
            # Check for expected keyword
            if monitor.expected_keyword:
                if monitor.expected_keyword.lower() not in response.text.lower():
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
                status_code=response.status_code,
                error_message=error_message,
                incident_type=incident_type,
            )
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    def check_tcp(self, monitor: MonitorConfig) -> CheckResult:
        """Perform TCP check"""
        start_time = time.time()
        try:
            # Parse host and port
            if ':' in monitor.target:
                host, port = monitor.target.split(':')
                port = int(port)
            else:
                host = monitor.target
                port = 80
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(monitor.timeout)
            result_code = sock.connect_ex((host, port))
            sock.close()
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            status = 'up' if result_code == 0 else 'down'
            error_message = None if result_code == 0 else f"TCP connection failed with code {result_code}"
            
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
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=response_time_ms,
                status_code=None,
                error_message=str(e),
                incident_type='downtime',
            )
    
    def perform_check(self, monitor: MonitorConfig) -> CheckResult:
        """Perform check based on monitor type"""
        if monitor.check_type in ['http', 'https']:
            return self.check_http(monitor)
        elif monitor.check_type == 'dns':
            return self.check_dns(monitor)
        elif monitor.check_type == 'custom':
            return self.check_custom(monitor)
        elif monitor.check_type == 'tcp':
            return self.check_tcp(monitor)
        else:
            return CheckResult(
                monitor_id=monitor.id,
                status='down',
                response_time_ms=None,
                status_code=None,
                error_message=f"Unknown check type: {monitor.check_type}",
                incident_type='downtime',
            )
    
    def submit_result(self, result: CheckResult):
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
            response = self.session.post(url, json=data, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error submitting result for monitor {result.monitor_id}: {e}", file=sys.stderr)
            return False
    
    def refresh_monitors(self):
        """Refresh monitor cache if expired"""
        if self.cache.is_expired():
            print(f"[{datetime.now()}] Refreshing monitor cache...")
            monitors = self.fetch_monitors()
            if monitors:
                self.cache.update(monitors)
                print(f"[{datetime.now()}] Loaded {len(monitors)} monitors")
            else:
                print(f"[{datetime.now()}] No monitors found or error occurred")
    
    def run_check_cycle(self):
        """Run a single check cycle for all monitors"""
        monitors = self.cache.get_monitors()
        
        if not monitors:
            print(f"[{datetime.now()}] No monitors to check")
            return
        
        print(f"[{datetime.now()}] Checking {len(monitors)} monitors...")
        
        for monitor in monitors.values():
            if not self.running:
                break
            
            try:
                result = self.perform_check(monitor)
                
                # Only submit if there's an incident (downtime or high latency)
                if result.incident_type:
                    self.submit_result(result)
                    print(f"[{datetime.now()}] Monitor {monitor.name}: {result.status} "
                          f"({result.response_time_ms}ms) - {result.incident_type}")
                else:
                    print(f"[{datetime.now()}] Monitor {monitor.name}: {result.status} "
                          f"({result.response_time_ms}ms)")
                
                # Wait a bit between checks to avoid overwhelming
                time.sleep(1)
            except Exception as e:
                print(f"[{datetime.now()}] Error checking monitor {monitor.name}: {e}", file=sys.stderr)
    
    def run(self, check_interval: int = 60):
        """Main run loop"""
        print(f"[{datetime.now()}] Starting region client for region: {self.region_code}")
        print(f"[{datetime.now()}] API URL: {self.api_base_url}")
        print(f"[{datetime.now()}] Check interval: {check_interval} seconds")
        print(f"[{datetime.now()}] Cache TTL: {self.cache.cache_ttl_minutes} minutes")
        
        # Initial monitor fetch
        self.refresh_monitors()
        
        last_check = {}
        
        while self.running:
            try:
                # Refresh cache if needed
                self.refresh_monitors()
                
                # Get monitors and check which ones need checking
                monitors = self.cache.get_monitors()
                now = time.time()
                
                monitors_to_check = []
                for monitor in monitors.values():
                    last_check_time = last_check.get(monitor.id, 0)
                    time_since_check = now - last_check_time
                    
                    # Check if it's time to check this monitor
                    if time_since_check >= monitor.check_interval:
                        monitors_to_check.append(monitor)
                
                # Perform checks
                for monitor in monitors_to_check:
                    if not self.running:
                        break
                    
                    try:
                        result = self.perform_check(monitor)
                        last_check[monitor.id] = now
                        
                        # Only submit if there's an incident
                        if result.incident_type:
                            self.submit_result(result)
                            print(f"[{datetime.now()}] Monitor {monitor.name}: {result.status} "
                                  f"({result.response_time_ms}ms) - {result.incident_type}")
                        else:
                            print(f"[{datetime.now()}] Monitor {monitor.name}: {result.status} "
                                  f"({result.response_time_ms}ms)")
                        
                        time.sleep(0.5)  # Small delay between checks
                    except Exception as e:
                        print(f"[{datetime.now()}] Error checking monitor {monitor.name}: {e}", file=sys.stderr)
                
                # Sleep until next cycle
                time.sleep(min(check_interval, 10))  # Check at least every 10 seconds
                
            except KeyboardInterrupt:
                print(f"\n[{datetime.now()}] Shutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"[{datetime.now()}] Error in main loop: {e}", file=sys.stderr)
                time.sleep(10)


def main():
    """Main entry point"""
    # Configuration from environment variables
    api_base_url = config('API_BASE_URL', default='http://localhost:8000')
    region_code = config('REGION_CODE', default='')
    api_key = config('API_KEY', default='')
    cache_ttl_minutes = config('CACHE_TTL_MINUTES', default=5, cast=int)
    check_interval = config('CHECK_INTERVAL', default=60, cast=int)
    
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
        client.run(check_interval)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
