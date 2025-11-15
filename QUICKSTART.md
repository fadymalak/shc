# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- Git

## Setup Steps

1. **Clone and navigate to the project**
```bash
cd /workspace
```

2. **Set up environment variables**
```bash
make setup
# Edit backend/.env if needed
```

3. **Start all services**
```bash
make up
```

4. **Run database migrations**
```bash
make migrate
```

5. **Create a superuser**
```bash
make createsuperuser
```

6. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin

## First Steps

1. **Register/Login**
   - Go to http://localhost:3000/login
   - Register a new account or login with your superuser credentials

2. **Create an Organization**
   - Navigate to Organizations
   - Create your first organization

3. **Add a Monitor**
   - Go to Monitors
   - Click "Add Monitor"
   - Configure your first monitor (e.g., HTTP check for https://example.com)

4. **Set up a Status Page**
   - Go to Status Pages
   - Create a status page for your organization
   - Add monitors to display

5. **Configure Regions** (Optional)
   - Go to Regions
   - Add regions where you've deployed custom clients

## API Usage Example

### Register a user
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user",
    "password": "securepassword",
    "password_confirm": "securepassword"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

### Create a monitor (with token)
```bash
curl -X POST http://localhost:8000/api/monitors/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -d '{
    "organization": 1,
    "name": "Example Monitor",
    "check_type": "http",
    "target": "https://example.com",
    "check_interval": 60,
    "high_latency_threshold": 5000
  }'
```

## Troubleshooting

### Services won't start
- Check if ports 3000, 8000, 5432, 6379 are available
- Check Docker logs: `make logs`

### Database connection errors
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database credentials in `backend/.env`

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check CORS settings in `backend/uptime_monitor/settings.py`

### Celery tasks not running
- Check Celery worker logs: `docker-compose logs celery`
- Ensure Redis is running: `docker-compose ps redis`

## Development Commands

```bash
# View logs
make logs

# Stop all services
make down

# Restart services
make down && make up

# Run Django shell
make shell

# Access backend container
make backend-shell

# Access frontend container
make frontend-shell
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API endpoints at http://localhost:8000/api/
- Check Django admin at http://localhost:8000/admin/
