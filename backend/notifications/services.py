"""
Notification services for Slack, Microsoft Teams, and Email
"""
import json
import aiohttp
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import NotificationChannel, NotificationLog


class NotificationService:
    """Base notification service"""
    
    def __init__(self, channel: NotificationChannel):
        self.channel = channel
    
    async def send(self, monitor, incident, notification_type: str) -> bool:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError


class SlackNotificationService(NotificationService):
    """Slack notification service"""
    
    async def send(self, monitor, incident, notification_type: str) -> bool:
        """Send Slack notification via webhook"""
        if not self.channel.slack_webhook_url:
            return False
        
        try:
            # Determine message based on notification type
            if notification_type == 'downtime':
                color = 'danger'
                title = f"🔴 Monitor Down: {monitor.name}"
                message = f"Monitor *{monitor.name}* is down.\n"
                if incident:
                    message += f"• Started: {incident.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                    if incident.error_message:
                        message += f"• Error: {incident.error_message}\n"
            elif notification_type == 'high_latency':
                color = 'warning'
                title = f"⚠️ High Latency: {monitor.name}"
                message = f"Monitor *{monitor.name}* is experiencing high latency.\n"
                if incident:
                    message += f"• Response time: {incident.response_time_ms}ms\n"
                    message += f"• Threshold: {monitor.high_latency_threshold}ms\n"
                    message += f"• Started: {incident.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            elif notification_type == 'resolved':
                color = 'good'
                title = f"✅ Monitor Resolved: {monitor.name}"
                message = f"Monitor *{monitor.name}* is back online.\n"
                if incident:
                    duration = incident.duration_seconds
                    if duration:
                        minutes = duration // 60
                        seconds = duration % 60
                        message += f"• Duration: {minutes}m {seconds}s\n"
                    message += f"• Resolved: {incident.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            else:
                return False
            
            # Build Slack payload
            payload = {
                "text": title,
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Monitor",
                                "value": monitor.name,
                                "short": True
                            },
                            {
                                "title": "Target",
                                "value": monitor.target,
                                "short": True
                            },
                            {
                                "title": "Details",
                                "value": message,
                                "short": False
                            }
                        ],
                        "footer": "Uptime Monitor",
                        "ts": int(timezone.now().timestamp())
                    }
                ]
            }
            
            # Add channel if specified
            if self.channel.slack_channel:
                payload["channel"] = self.channel.slack_channel
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.channel.slack_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        raise Exception(f"Slack API error: {response.status} - {error_text}")
        
        except Exception as e:
            # Log error
            NotificationLog.objects.create(
                channel=self.channel,
                monitor=monitor,
                incident=incident,
                notification_type=notification_type,
                status='failed',
                error_message=str(e)
            )
            return False


class TeamsNotificationService(NotificationService):
    """Microsoft Teams notification service"""
    
    async def send(self, monitor, incident, notification_type: str) -> bool:
        """Send Microsoft Teams notification via webhook"""
        if not self.channel.teams_webhook_url:
            return False
        
        try:
            # Determine theme color and title
            if notification_type == 'downtime':
                theme_color = "FF0000"
                title = f"🔴 Monitor Down: {monitor.name}"
                summary = f"Monitor {monitor.name} is down"
            elif notification_type == 'high_latency':
                theme_color = "FFA500"
                title = f"⚠️ High Latency: {monitor.name}"
                summary = f"Monitor {monitor.name} is experiencing high latency"
            elif notification_type == 'resolved':
                theme_color = "00FF00"
                title = f"✅ Monitor Resolved: {monitor.name}"
                summary = f"Monitor {monitor.name} is back online"
            else:
                return False
            
            # Build facts
            facts = [
                {"name": "Monitor", "value": monitor.name},
                {"name": "Target", "value": monitor.target},
            ]
            
            if incident:
                if notification_type == 'downtime':
                    facts.append({
                        "name": "Started",
                        "value": incident.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                    })
                    if incident.error_message:
                        facts.append({"name": "Error", "value": incident.error_message})
                elif notification_type == 'high_latency':
                    facts.append({
                        "name": "Response Time",
                        "value": f"{incident.response_time_ms}ms"
                    })
                    facts.append({
                        "name": "Threshold",
                        "value": f"{monitor.high_latency_threshold}ms"
                    })
                elif notification_type == 'resolved':
                    if incident.duration_seconds:
                        minutes = incident.duration_seconds // 60
                        seconds = incident.duration_seconds % 60
                        facts.append({
                            "name": "Duration",
                            "value": f"{minutes}m {seconds}s"
                        })
                    if incident.resolved_at:
                        facts.append({
                            "name": "Resolved",
                            "value": incident.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                        })
            
            # Build Teams message card
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": summary,
                "themeColor": theme_color,
                "title": title,
                "sections": [
                    {
                        "activityTitle": title,
                        "facts": facts,
                        "markdown": True
                    }
                ]
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.channel.teams_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        raise Exception(f"Teams API error: {response.status} - {error_text}")
        
        except Exception as e:
            # Log error
            NotificationLog.objects.create(
                channel=self.channel,
                monitor=monitor,
                incident=incident,
                notification_type=notification_type,
                status='failed',
                error_message=str(e)
            )
            return False


class EmailNotificationService(NotificationService):
    """Email notification service"""
    
    def send_sync(self, monitor, incident, notification_type: str) -> bool:
        """Send email notification"""
        if not self.channel.email_addresses:
            return False
        
        try:
            # Parse email addresses
            email_list = [email.strip() for email in self.channel.email_addresses.split(',')]
            
            # Determine subject and context
            if notification_type == 'downtime':
                subject = f"🔴 Monitor Down: {monitor.name}"
                context = {
                    'monitor': monitor,
                    'incident': incident,
                    'notification_type': 'downtime',
                    'title': 'Monitor Down',
                }
            elif notification_type == 'high_latency':
                subject = f"⚠️ High Latency: {monitor.name}"
                context = {
                    'monitor': monitor,
                    'incident': incident,
                    'notification_type': 'high_latency',
                    'title': 'High Latency Detected',
                }
            elif notification_type == 'resolved':
                subject = f"✅ Monitor Resolved: {monitor.name}"
                context = {
                    'monitor': monitor,
                    'incident': incident,
                    'notification_type': 'resolved',
                    'title': 'Monitor Resolved',
                }
            else:
                return False
            
            # Render email template
            html_message = render_to_string('notifications/email_notification.html', context)
            plain_message = render_to_string('notifications/email_notification.txt', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@uptimemonitor.com'),
                recipient_list=email_list,
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
        
        except Exception as e:
            # Log error
            NotificationLog.objects.create(
                channel=self.channel,
                monitor=monitor,
                incident=incident,
                notification_type=notification_type,
                status='failed',
                error_message=str(e)
            )
            return False
    
    async def send(self, monitor, incident, notification_type: str) -> bool:
        """Async wrapper for sync email sending"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_sync, monitor, incident, notification_type)


def get_notification_service(channel: NotificationChannel) -> NotificationService:
    """Get appropriate notification service for channel type"""
    if channel.channel_type == 'slack':
        return SlackNotificationService(channel)
    elif channel.channel_type == 'teams':
        return TeamsNotificationService(channel)
    elif channel.channel_type == 'email':
        return EmailNotificationService(channel)
    else:
        raise ValueError(f"Unknown channel type: {channel.channel_type}")
