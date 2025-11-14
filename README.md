# Uptime Monitoring SaaS Platform

A comprehensive uptime monitoring SaaS platform built with Django, PostgreSQL, DRF, and React.

## Features

### Core Features

1. **Incident Tracking**: Stores only downtime and high latency issues (not all checks)
2. **Status Pages**: Public status pages that users can attach to subdomains
3. **Organization Management**: Multi-tenant organization system with role-based access control
   - **Owner**: Full access (view, edit, delete, manage members, manage settings)
   - **Project Lead**: View, edit, manage members
   - **Developer**: View only
4. **Region Tracking**: Deploy custom clients on servers in different regions to test domains from multiple geographic locations
5. **TLS Certificate Monitoring**: Automatic tracking and notifications when certificates are near expiration
6. **Multiple Check Types**:
   - **HTTP/HTTPS**: Monitor web endpoints with status code validation
   - **DNS**: Check DNS records (A, AAAA, MX, etc.)
   - **Custom**: Check for specific keywords in HTTP response
   - **TCP**: Test TCP connectivity

## Tech Stack

### Backend
- **Django 4.2**: Web framework
- **PostgreSQL**: Database
- **Django REST Framework**: API
- **Celery**: Background task processing
- **Redis**: Message broker and cache

### Frontend
- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **React Query**: Data fetching
- **React Router**: Routing

## Project Structure

```
/workspace/
├── backend/                 # Django backend
│   ├── organizations/      # Organization and user management
│   ├── monitors/           # Monitor configuration and checks
│   ├── incidents/          # Incident tracking (downtime/high latency)
│   ├── status_pages/       # Public status pages
│   ├── regions/            # Region/client management
│   ├── certificates/       # TLS certificate tracking
│   └── uptime_monitor/     # Django project settings
├── frontend/               # React frontend
│   └── src/
│       ├── components/     # Reusable components
│       ├── pages/          # Page components
│       └── store/          # State management
└── docker-compose.yml      # Docker orchestration
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- PostgreSQL 15+
- Redis

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd uptime-monitor
```

2. **Set up environment variables**

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

3. **Start with Docker Compose**

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis
- Django backend (port 8000)
- Celery worker
- Celery beat (scheduler)
- React frontend (port 3000)

4. **Run migrations**

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up .env file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run Celery worker (in separate terminal)
celery -A uptime_monitor worker -l info

# Run Celery beat (in separate terminal)
celery -A uptime_monitor beat -l info
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login

### Organizations
- `GET /api/organizations/` - List organizations
- `POST /api/organizations/` - Create organization
- `GET /api/organizations/{id}/` - Get organization details
- `PATCH /api/organizations/{id}/` - Update organization
- `POST /api/organizations/{id}/add_member/` - Add member to organization

### Monitors
- `GET /api/monitors/` - List monitors
- `POST /api/monitors/` - Create monitor
- `GET /api/monitors/{id}/` - Get monitor details
- `PATCH /api/monitors/{id}/` - Update monitor
- `DELETE /api/monitors/{id}/` - Delete monitor
- `POST /api/monitors/{id}/pause/` - Pause monitor
- `POST /api/monitors/{id}/resume/` - Resume monitor

### Incidents
- `GET /api/incidents/` - List incidents
- `GET /api/incidents/{id}/` - Get incident details
- `POST /api/incidents/{id}/resolve/` - Resolve incident
- `GET /api/incidents/stats/` - Get incident statistics

### Status Pages
- `GET /api/status-pages/` - List status pages
- `POST /api/status-pages/` - Create status page
- `GET /api/status-pages/{id}/public/` - Public status page view
- `GET /api/status-pages/by-subdomain/{subdomain}/` - Get by subdomain

### Regions
- `GET /api/regions/` - List regions
- `POST /api/regions/` - Create region
- `GET /api/regions/{id}/` - Get region details

### Certificates
- `GET /api/certificates/` - List certificates
- `GET /api/certificates/expiring_soon/` - Get expiring certificates
- `POST /api/certificates/{id}/mark_notification_sent/` - Mark notification sent

## Usage

### Creating a Monitor

1. Navigate to Monitors page
2. Click "Add Monitor"
3. Fill in:
   - Name
   - Check type (HTTP, DNS, Custom, TCP)
   - Target URL/domain
   - Check interval
   - High latency threshold
   - Regions to check from

### Setting Up a Status Page

1. Navigate to Status Pages
2. Click "Create Status Page"
3. Configure:
   - Title and description
   - Subdomain
   - Custom domain (optional)
   - Select monitors to display
   - Theme customization

### Adding Regions

1. Navigate to Regions
2. Click "Add Region"
3. Provide:
   - Region name and code
   - Location
   - Client endpoint URL
   - API key for authentication

## Monitoring Checks

Monitors are checked periodically based on their `check_interval` setting. The system:

1. Performs the check based on monitor type
2. **Only creates incidents** if:
   - Service is down (downtime)
   - Response time exceeds threshold (high latency)
3. Tracks TLS certificates for HTTPS monitors
4. Sends notifications for expiring certificates

## Certificate Expiration Notifications

Certificates are automatically checked when HTTPS monitors are verified. Notifications are sent when:
- Certificate expires within configured warning days (default: 30)
- Notification hasn't been sent recently (weekly reminder)

## Custom Region Clients

To deploy custom clients in different regions:

1. Create a Region in the dashboard
2. Deploy your custom client application that:
   - Accepts check requests via API
   - Performs checks from that region
   - Returns results to the main platform
3. Configure the region with the client endpoint and API key

## Development

### Running Tests

```bash
cd backend
python manage.py test
```

### Code Style

Backend follows PEP 8. Frontend uses ESLint and Prettier.

## License

[Your License Here]

## Contributing

[Contributing Guidelines]
