"""
Celery tasks for sending notifications
"""
from celery import shared_task
from django.utils import timezone
from .models import NotificationChannel, MonitorNotificationPreference, NotificationLog
from .services import get_notification_service
import asyncio


@shared_task
def send_notification(channel_id, monitor_id, incident_id, notification_type):
    """Send notification for an incident"""
    try:
        channel = NotificationChannel.objects.get(id=channel_id, is_active=True)
        from monitors.models import Monitor
        monitor = Monitor.objects.get(id=monitor_id)
        from incidents.models import Incident
        incident = Incident.objects.get(id=incident_id) if incident_id else None
        
        # Check if notification should be sent
        if notification_type == 'downtime' and not channel.notify_on_downtime:
            return False
        if notification_type == 'high_latency' and not channel.notify_on_high_latency:
            return False
        if notification_type == 'resolved' and not channel.notify_on_resolution:
            return False
        
        # Check monitor-specific preferences
        try:
            pref = MonitorNotificationPreference.objects.get(
                monitor=monitor,
                channel=channel
            )
            if not pref.is_enabled:
                return False
            if notification_type == 'downtime' and not pref.notify_on_downtime:
                return False
            if notification_type == 'high_latency' and not pref.notify_on_high_latency:
                return False
            if notification_type == 'resolved' and not pref.notify_on_resolution:
                return False
        except MonitorNotificationPreference.DoesNotExist:
            # Use channel defaults if no monitor-specific preference
            pass
        
        # Create notification log
        log = NotificationLog.objects.create(
            channel=channel,
            monitor=monitor,
            incident=incident,
            notification_type=notification_type,
            status='pending'
        )
        
        # Get notification service and send
        service = get_notification_service(channel)
        
        # Run async send (email service has async wrapper)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                service.send(monitor, incident, notification_type)
            )
            
            if success:
                log.status = 'sent'
                log.sent_at = timezone.now()
                log.save()
            else:
                log.status = 'failed'
                log.error_message = "Notification service returned False"
                log.save()
            
            return success
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            return False
        finally:
            loop.close()
        
    except Exception as e:
        # Log error
        try:
            log = NotificationLog.objects.get(id=log.id)
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
        except:
            pass
        return False


@shared_task
def send_notifications_for_incident(incident_id, notification_type):
    """Send notifications to all channels for an incident"""
    try:
        from incidents.models import Incident
        incident = Incident.objects.get(id=incident_id)
        monitor = incident.monitor
        
        # Get all active channels for the organization
        channels = NotificationChannel.objects.filter(
            organization=monitor.organization,
            is_active=True
        )
        
        # Send notification to each channel
        for channel in channels:
            send_notification.delay(
                channel.id,
                monitor.id,
                incident.id,
                notification_type
            )
        
        return True
    except Exception as e:
        return False
