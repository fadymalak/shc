"""
Signals for triggering notifications
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from incidents.models import Incident
from .tasks import send_notifications_for_incident


@receiver(post_save, sender=Incident)
def notify_on_incident(sender, instance, created, **kwargs):
    """Send notifications when incident is created or updated"""
    if created:
        # New incident - send downtime or high latency notification
        if instance.incident_type == 'downtime':
            send_notifications_for_incident.delay(instance.id, 'downtime')
        elif instance.incident_type == 'high_latency':
            send_notifications_for_incident.delay(instance.id, 'high_latency')
    else:
        # Updated incident - check if resolved
        if instance.status == 'resolved' and instance.resolved_at:
            # Check if this is a new resolution (not already notified)
            from .models import NotificationLog
            already_notified = NotificationLog.objects.filter(
                incident=instance,
                notification_type='resolved',
                status='sent'
            ).exists()
            
            if not already_notified:
                send_notifications_for_incident.delay(instance.id, 'resolved')
