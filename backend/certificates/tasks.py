from celery import shared_task
from django.utils import timezone
from .models import Certificate


@shared_task
def send_certificate_expiry_notification(certificate_id):
    """Send notification for expiring certificate"""
    try:
        certificate = Certificate.objects.get(id=certificate_id)
        
        if certificate.needs_notification:
            # Get organization members to notify
            if certificate.monitor and certificate.monitor.organization:
                organization = certificate.monitor.organization
                members = organization.members.filter(is_active=True)
                
                # TODO: Implement actual notification sending
                # This could be email, Slack, webhook, etc.
                # For now, just mark as sent
                certificate.notification_sent = True
                certificate.last_notification_sent_at = timezone.now()
                certificate.save()
                
                # Example: Send email to all organization members
                # for member in members:
                #     send_email_notification(member.user.email, certificate)
                
    except Certificate.DoesNotExist:
        pass
