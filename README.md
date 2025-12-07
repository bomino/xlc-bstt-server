# BSTT Compliance Dashboard

A modern web application for tracking and analyzing biometric time tracking compliance across multiple XLC offices. Built with Django REST Framework and React TypeScript, deployed via Docker.

## Features

### Dashboard & Analytics
- **Executive Dashboard**: Real-time KPIs including finger scan rates, provisional entries, write-ins, and missing clock-outs
- **Office Analysis**: Compare compliance metrics across offices with ranking, department, and shift breakdowns
- **Entry Type Analysis**: Visualize distribution of entry types with weekly trends
- **Employee Analysis**: Track individual employee compliance and identify enrollment needs
- **Weekly Trends**: Historical compliance data with week-over-week comparisons (ISO week aligned)
- **Clock Behavior**: Analyze clock-in/out attempts and identify training needs
- **Data Explorer**: Browse and export raw time entry data
- **ISO Week Alignment**: Properly counts unique weeks across offices with different week endings (Martinsburg Saturday, others Sunday)

### Admin Features
- **Data Upload**: Upload CSV/Excel files with visual progress monitoring (3-stage workflow with progress bar)
- **Database Management**: Clear data by year or reset entire database with confirmation dialogs
- **User Management**: Django auth with User/Group administration
- **Excel Report Generation**: Export comprehensive reports matching BSTT-rpt.xlsx format (12+ sheets)

## Tech Stack

### Backend
- Python 3.11+
- Django 4.2+
- Django REST Framework
- SQLite (development) / PostgreSQL (production)
- Pandas for data processing
- OpenPyXL for Excel generation
- WhiteNoise for static files

### Frontend
- React 18 with TypeScript
- Recharts for data visualization
- Tailwind CSS for styling
- Axios for API communication
- Lucide React for icons

### Infrastructure
- Docker & Docker Compose
- Nginx reverse proxy
- Gunicorn WSGI server

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/your-org/bstt-web.git
cd bstt-web
```

2. Build and run:
```bash
docker-compose up --build
```

3. Create admin user:
```bash
docker-compose exec backend python manage.py createsuperuser
```

4. Access the application:
- **Frontend Dashboard**: http://localhost/
- **Admin Panel**: http://localhost/admin/
- **Upload Data**: http://localhost/admin/core/dataupload/add/
- **Database Management**: http://localhost/admin/database-management/
- **API**: http://localhost/api/

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Load initial data (if available)
python manage.py sync_csv --year 2025

# Start development server
python manage.py runserver 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Project Structure

```
BSTT-Web/
├── backend/                 # Django backend
│   ├── config/             # Django project settings
│   ├── core/               # Core app (models, admin, services)
│   │   ├── models.py       # TimeEntry, DataUpload, ETLHistory
│   │   ├── admin.py        # Custom BSTTAdminSite
│   │   ├── services.py     # File upload processing
│   │   └── templates/      # Admin templates (upload progress UI)
│   ├── kpis/               # KPI calculations and API
│   │   └── calculator.py   # 35+ KPI calculations
│   ├── reports/            # Excel report generation
│   │   └── generators.py   # Multi-sheet report generator
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # Axios API client
│   │   ├── components/    # Reusable components
│   │   │   └── layout/    # AppLayout, Sidebar, FilterBar
│   │   ├── contexts/      # FilterContext
│   │   ├── pages/         # Dashboard, OfficeAnalysis, etc.
│   │   ├── constants/     # Colors, thresholds
│   │   └── types/         # TypeScript interfaces
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf         # Nginx reverse proxy config
├── docker-compose.yml
├── CLAUDE.md              # Development guidelines
└── README.md
```

## API Endpoints

### KPIs
| Endpoint | Description |
|----------|-------------|
| `GET /api/kpis/` | Aggregate KPIs with filters |
| `GET /api/kpis/by-office/` | KPIs grouped by office |
| `GET /api/kpis/by-week/` | Weekly KPI trends |
| `GET /api/kpis/by-department/` | KPIs by department |
| `GET /api/kpis/by-shift/` | KPIs by shift |
| `GET /api/kpis/by-employee/` | Employee-level metrics |
| `GET /api/kpis/clock-behavior/` | Clock attempt analysis |

### Data
| Endpoint | Description |
|----------|-------------|
| `GET /api/time-entries/` | Paginated time entries |
| `GET /api/filters/options/` | Available filter options |
| `GET /api/data-quality/` | Data freshness indicators |
| `GET /api/health/` | Health check endpoint |

### Reports
| Endpoint | Description |
|----------|-------------|
| `GET /api/reports/full/` | Download full Excel report |

## Admin Panel Features

### Data Upload (`/admin/core/dataupload/add/`)
Visual upload interface with:
- Real-time upload progress bar (0-100%)
- File name and size display
- 3-stage workflow indicator (Upload → Process → Complete)
- Processing animation during database import
- Success/error messages

### Database Management (`/admin/database-management/`)
- View record counts by model and year
- Clear time entries for a specific year
- Reset entire database (with confirmation)
- Delete confirmation dialogs with typed confirmation

### User Management
- Create/edit users and groups
- Manage staff and superuser permissions
- Session management

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Django debug mode | `False` |
| `SECRET_KEY` | Django secret key | Required |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost` |
| `CORS_ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |

### KPI Thresholds

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Finger Rate | ≥95% | 90-95% | <90% |
| Provisional Rate | <1% | 1-3% | >3% |
| Write-In Rate | <3% | 3-5% | >5% |
| Missing C/O Rate | <2% | 2-5% | >5% |

## Data Import

### Via Django Admin
1. Navigate to Admin Panel → Data uploads → Add
2. Select CSV or Excel file
3. Choose year and file type
4. Click Save to upload and process

### Via Command Line
```bash
# From CSV files in output directory
python manage.py sync_csv --year 2025

# In Docker
docker-compose exec backend python manage.py sync_csv --year 2025
```

## Development

### Running Tests

```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
npm test
```

### Code Style

- **Backend**: PEP 8, docstrings for functions
- **Frontend**: ESLint + Prettier, TypeScript strict mode

### Docker Commands

```bash
# Start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose up -d --build backend

# Execute commands in container
docker-compose exec backend python manage.py migrate

# Stop containers
docker-compose down
```

## Deployment

Choose your deployment method:

| Method | Best For | Database | SSL |
|--------|----------|----------|-----|
| **Docker Compose** | VPS, bare metal | SQLite/PostgreSQL | Manual (nginx) |
| **Railway** | Quick deploy, teams | PostgreSQL | Automatic |
| **Render** | Static + API apps | PostgreSQL | Automatic |
| **Fly.io** | Global edge, scaling | PostgreSQL | Automatic |

### Option A: Docker Compose (VPS/Self-Hosted)

Best for: Full control, existing infrastructure, on-premise deployment.

#### Production Deployment Steps

1. **Generate a secret key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

2. **Create `.env.production`** (copy from `.env.example` and update values):
```bash
SECRET_KEY=<your-generated-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

3. **Set up SSL certificates** in `nginx/ssl/` (see `nginx/README.md` for detailed instructions):
```bash
# Option A: Let's Encrypt (recommended)
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# Option B: Self-signed (for internal/testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=your-domain.com"
```

4. **Build and deploy:**
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up --build -d
```

5. **Create admin user:**
```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

6. **Set up daily backups** (add to crontab):
```bash
chmod +x scripts/backup.sh
# Add to crontab: 0 2 * * * /path/to/bstt-web/scripts/backup.sh
```

### Production Checklist

- [ ] Generate unique SECRET_KEY (64+ characters)
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS for your domain
- [ ] Set up SSL certificates in nginx/ssl/
- [ ] Configure CORS_ALLOWED_ORIGINS
- [ ] Create admin superuser
- [ ] Set up daily backup cron job
- [ ] Test health endpoints (https://your-domain.com/api/health/)

### Backup and Restore

```bash
# Create backup
./scripts/backup.sh

# Restore from latest backup
./scripts/backup.sh --restore

# List available backups
./scripts/backup.sh --list
```

### Option B: Railway (Quick Deploy)

Best for: Teams, quick deployment, automatic SSL.

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and initialize
railway login
railway init

# 3. Add PostgreSQL database
railway add --database postgres

# 4. Set environment variables
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set CORS_ALLOWED_ORIGINS=https://your-app.railway.app

# 5. Deploy
railway up
```

See [docs/PAAS_DEPLOYMENT.md](docs/PAAS_DEPLOYMENT.md) for detailed Railway instructions.

### Option C: Render (Static + API)

Best for: Separate static hosting, free tier available.

1. Connect your GitHub repository to Render
2. Create a new Web Service for the backend
3. Create a PostgreSQL database
4. Create a Static Site for the frontend

See [docs/PAAS_DEPLOYMENT.md](docs/PAAS_DEPLOYMENT.md) for detailed Render instructions and `render.yaml` blueprint.

### Option D: Fly.io (Global Edge)

Best for: Global distribution, edge computing.

```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login and launch
fly auth login
fly launch

# 3. Create PostgreSQL database
fly postgres create --name bstt-db
fly postgres attach bstt-db

# 4. Deploy
fly deploy
```

See [docs/PAAS_DEPLOYMENT.md](docs/PAAS_DEPLOYMENT.md) for detailed Fly.io instructions.

## Troubleshooting

### Port Conflict
If localhost:8000 times out:
```powershell
netstat -ano | findstr ":8000.*LISTENING"
taskkill /PID <pid> /F
```

### Docker Issues
```bash
# Rebuild everything
docker-compose down
docker-compose up --build

# Check logs
docker-compose logs backend
docker-compose logs frontend
```

### Static Files Not Loading
```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

## License

Proprietary - XLC Services

## Support

For issues and feature requests, contact the development team.
