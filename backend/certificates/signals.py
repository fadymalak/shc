from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Certificate
from .tasks import send_certificate_expiry_notification


@receiver(post_save, sender=Certificate)
def check_certificate_expiry(sender, instance, created, **kwargs):
    """Signal to send notification when certificate is expiring soon"""
    if instance.needs_notification:
        send_certificate_expiry_notification.delay(instance.id)
