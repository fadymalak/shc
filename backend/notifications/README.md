# Notifications System

Notification system for sending alerts to Slack, Microsoft Teams, and Email when monitors go down or experience high latency.

## Features

- **Multiple Channels**: Support for Slack, Microsoft Teams, and Email
- **Flexible Configuration**: Per-channel and per-monitor notification preferences
- **Event Types**: Notify on downtime, high latency, and resolution
- **Async Delivery**: Uses Celery for async notification delivery
- **Notification Logging**: Tracks all sent notifications

## Setup

### Slack Integration

1. **Create Slack Webhook**:
   - Go to https://api.slack.com/apps
   - Create a new app or select existing
   - Go to "Incoming Webhooks"
   - Activate incoming webhooks
   - Add new webhook to workspace
   - Copy webhook URL

2. **Configure in Dashboard**:
   - Go to Notifications
   - Create new Slack channel
   - Paste webhook URL
   - Optionally specify channel name

### Microsoft Teams Integration

1. **Create Teams Webhook**:
   - Open Teams channel
   - Click "..." → Connectors
   - Search for "Incoming Webhook"
   - Configure and create
   - Copy webhook URL

2. **Configure in Dashboard**:
   - Go to Notifications
   - Create new Teams channel
   - Paste webhook URL

### Email Integration

1. **Configure SMTP Settings**:
   - Update `.env` file with email settings:
     ```
     EMAIL_HOST=smtp.gmail.com
     EMAIL_PORT=587
     EMAIL_USE_TLS=True
     EMAIL_HOST_USER=your-email@gmail.com
     EMAIL_HOST_PASSWORD=your-app-password
     DEFAULT_FROM_EMAIL=noreply@uptimemonitor.com
     ```

2. **Configure in Dashboard**:
   - Go to Notifications
   - Create new Email channel
   - Enter comma-separated email addresses

## Usage

### Creating Notification Channels

1. Navigate to Notifications page
2. Click "Add Channel"
3. Select channel type (Slack, Teams, or Email)
4. Configure channel-specific settings
5. Set notification preferences (downtime, high latency, resolution)
6. Save

### Per-Monitor Preferences

You can override channel defaults for specific monitors:
- Go to Monitor details
- Configure notification preferences
- Select which channels to use for this monitor

### Testing

Use the "Test" button on any channel to send a test notification.

## Notification Types

### Downtime
- Triggered when monitor goes down
- Includes error message and start time
- Red color/theme in Slack and Teams

### High Latency
- Triggered when response time exceeds threshold
- Includes response time and threshold
- Yellow/orange color/theme

### Resolution
- Triggered when incident is resolved
- Includes duration and resolution time
- Green color/theme

## API Endpoints

- `GET /api/notifications/channels/` - List notification channels
- `POST /api/notifications/channels/` - Create channel
- `GET /api/notifications/channels/{id}/` - Get channel details
- `PATCH /api/notifications/channels/{id}/` - Update channel
- `POST /api/notifications/channels/{id}/test/` - Test channel
- `GET /api/notifications/logs/` - View notification logs

## Troubleshooting

### Notifications Not Sending

1. Check Celery worker is running
2. Check notification logs for errors
3. Verify channel configuration
4. Test channel using test button

### Email Not Working

1. Verify SMTP settings in `.env`
2. Check email server allows connections
3. For Gmail, use App Password (not regular password)
4. Check spam folder

### Slack/Teams Not Working

1. Verify webhook URL is correct
2. Check webhook hasn't been revoked
3. Verify channel permissions
4. Check notification logs for API errors
