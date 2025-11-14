from celery import shared_task
from django.utils import timezone
from django.conf import settings
import requests
import dns.resolver
import socket
from .models import Monitor
from incidents.models import Incident
from certificates.models import Certificate
import ssl
from datetime import datetime


@shared_task
def check_monitor(monitor_id, region_id=None):
    """Check a monitor and create incidents if downtime or high latency detected"""
    try:
        monitor = Monitor.objects.get(id=monitor_id, is_active=True, is_paused=False)
        
        if region_id:
            from regions.models import Region
            region = Region.objects.get(id=region_id)
        else:
            region = None
        
        result = perform_check(monitor, region)
        
        # Only create incident if there's downtime or high latency
        if result['status'] == 'down' or result['incident_type']:
            create_incident(monitor, region, result)
        
        # Check certificate if HTTPS monitor
        if monitor.check_type in ['https', 'http'] and 'https://' in monitor.target:
            check_certificate(monitor)
        
        return result
        
    except Monitor.DoesNotExist:
        return {'error': 'Monitor not found'}


def perform_check(monitor, region=None):
    """Perform the actual check based on monitor type"""
    start_time = timezone.now()
    result = {
        'status': 'up',
        'response_time_ms': None,
        'status_code': None,
        'error_message': None,
        'incident_type': None,
    }
    
    try:
        if monitor.check_type in ['http', 'https']:
            result = check_http(monitor)
        elif monitor.check_type == 'dns':
            result = check_dns(monitor)
        elif monitor.check_type == 'custom':
            result = check_custom(monitor)
        elif monitor.check_type == 'tcp':
            result = check_tcp(monitor)
        
        # Calculate response time
        end_time = timezone.now()
        if result.get('response_time_ms'):
            response_time = result['response_time_ms']
        else:
            response_time = int((end_time - start_time).total_seconds() * 1000)
            result['response_time_ms'] = response_time
        
        # Check for high latency
        if response_time > monitor.high_latency_threshold:
            result['incident_type'] = 'high_latency'
            result['status'] = 'high_latency'
        
    except Exception as e:
        result['status'] = 'down'
        result['incident_type'] = 'downtime'
        result['error_message'] = str(e)
    
    return result


def check_http(monitor):
    """Check HTTP/HTTPS endpoint"""
    result = {
        'status': 'up',
        'response_time_ms': None,
        'status_code': None,
        'error_message': None,
    }
    
    try:
        start = timezone.now()
        response = requests.get(
            monitor.target,
            timeout=monitor.timeout,
            allow_redirects=True,
            verify=True
        )
        end = timezone.now()
        
        response_time = int((end - start).total_seconds() * 1000)
        result['response_time_ms'] = response_time
        result['status_code'] = response.status_code
        
        # Check expected status code
        if monitor.expected_status_code and response.status_code != monitor.expected_status_code:
            result['status'] = 'down'
            result['error_message'] = f"Expected status {monitor.expected_status_code}, got {response.status_code}"
        
    except requests.exceptions.RequestException as e:
        result['status'] = 'down'
        result['error_message'] = str(e)
    
    return result


def check_dns(monitor):
    """Check DNS record"""
    result = {
        'status': 'up',
        'response_time_ms': None,
        'error_message': None,
    }
    
    try:
        start = timezone.now()
        resolver = dns.resolver.Resolver()
        resolver.timeout = monitor.timeout
        resolver.lifetime = monitor.timeout
        
        record_type = monitor.dns_record_type or 'A'
        answers = resolver.resolve(monitor.target, record_type)
        
        end = timezone.now()
        response_time = int((end - start).total_seconds() * 1000)
        result['response_time_ms'] = response_time
        
        # Check expected DNS record
        if monitor.expected_dns_record:
            found = False
            for answer in answers:
                if str(answer) == monitor.expected_dns_record:
                    found = True
                    break
            if not found:
                result['status'] = 'down'
                result['error_message'] = f"Expected DNS record {monitor.expected_dns_record} not found"
        
    except Exception as e:
        result['status'] = 'down'
        result['error_message'] = str(e)
    
    return result


def check_custom(monitor):
    """Check custom keyword in HTTP response"""
    result = {
        'status': 'up',
        'response_time_ms': None,
        'error_message': None,
    }
    
    try:
        start = timezone.now()
        response = requests.get(
            monitor.target,
            timeout=monitor.timeout,
            allow_redirects=True
        )
        end = timezone.now()
        
        response_time = int((end - start).total_seconds() * 1000)
        result['response_time_ms'] = response_time
        
        # Check for expected keyword
        if monitor.expected_keyword:
            if monitor.expected_keyword.lower() not in response.text.lower():
                result['status'] = 'down'
                result['error_message'] = f"Expected keyword '{monitor.expected_keyword}' not found in response"
        
    except requests.exceptions.RequestException as e:
        result['status'] = 'down'
        result['error_message'] = str(e)
    
    return result


def check_tcp(monitor):
    """Check TCP connection"""
    result = {
        'status': 'up',
        'response_time_ms': None,
        'error_message': None,
    }
    
    try:
        # Parse host and port from target (format: host:port)
        if ':' in monitor.target:
            host, port = monitor.target.split(':')
            port = int(port)
        else:
            host = monitor.target
            port = 80
        
        start = timezone.now()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(monitor.timeout)
        result_code = sock.connect_ex((host, port))
        sock.close()
        end = timezone.now()
        
        response_time = int((end - start).total_seconds() * 1000)
        result['response_time_ms'] = response_time
        
        if result_code != 0:
            result['status'] = 'down'
            result['error_message'] = f"TCP connection failed with code {result_code}"
        
    except Exception as e:
        result['status'] = 'down'
        result['error_message'] = str(e)
    
    return result


def create_incident(monitor, region, check_result):
    """Create incident if downtime or high latency detected"""
    incident_type = check_result.get('incident_type')
    
    if not incident_type:
        return
    
    # Check if there's already an open incident of this type
    existing_incident = Incident.objects.filter(
        monitor=monitor,
        region=region,
        incident_type=incident_type,
        status='open'
    ).first()
    
    if existing_incident:
        # Update existing incident
        existing_incident.response_time_ms = check_result.get('response_time_ms')
        existing_incident.status_code = check_result.get('status_code')
        existing_incident.error_message = check_result.get('error_message')
        existing_incident.save()
    else:
        # Create new incident
        Incident.objects.create(
            monitor=monitor,
            region=region,
            incident_type=incident_type,
            status='open',
            started_at=timezone.now(),
            response_time_ms=check_result.get('response_time_ms'),
            status_code=check_result.get('status_code'),
            error_message=check_result.get('error_message'),
        )


def check_certificate(monitor):
    """Check TLS certificate for HTTPS monitors"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(monitor.target)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Get certificate
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
        
        # Parse certificate dates
        valid_from = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
        valid_until = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        
        # Convert to timezone-aware datetime
        from django.utils import timezone
        valid_from = timezone.make_aware(valid_from)
        valid_until = timezone.make_aware(valid_until)
        
        # Get or create certificate record
        certificate, created = Certificate.objects.get_or_create(
            domain=domain,
            monitor=monitor,
            defaults={
                'issuer': cert.get('issuer', [[('CN', 'Unknown')]])[0][0][1],
                'subject': cert.get('subject', [[('CN', 'Unknown')]])[0][0][1],
                'serial_number': cert.get('serialNumber', ''),
                'valid_from': valid_from,
                'valid_until': valid_until,
            }
        )
        
        if not created:
            # Update existing certificate
            certificate.issuer = cert.get('issuer', [[('CN', 'Unknown')]])[0][0][1]
            certificate.subject = cert.get('subject', [[('CN', 'Unknown')]])[0][0][1]
            certificate.serial_number = cert.get('serialNumber', '')
            certificate.valid_from = valid_from
            certificate.valid_until = valid_until
            certificate.save()
        
    except Exception as e:
        # Certificate check failed, but don't create incident for this
        print(f"Certificate check failed for {monitor.target}: {e}")


@shared_task
def check_all_monitors():
    """Periodic task to check all active monitors"""
    monitors = Monitor.objects.filter(is_active=True, is_paused=False)
    
    for monitor in monitors:
        # Check from all assigned regions
        if monitor.regions.exists():
            for region in monitor.regions.filter(is_active=True):
                check_monitor.delay(monitor.id, region.id)
        else:
            # Check from default (no region)
            check_monitor.delay(monitor.id)
