# BSTT Application Setup Guide (Windows Server)

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Node.js 16+** - [Download from nodejs.org](https://nodejs.org/)
   - This includes npm (Node Package Manager)

3. **Git** (optional) - For version control

## Quick Start

### First-Time Setup

1. **Run the setup script** (one-time only):
   ```
   setup-first-time.bat
   ```

   This will:
   - Check Python and Node.js installations
   - Create Python virtual environment
   - Install all backend dependencies
   - Run database migrations
   - Create admin user (you'll be prompted)
   - Install frontend dependencies

2. **Start the application**:
   ```
   start-all.bat
   ```

   This opens two command windows:
   - Backend server (Django)
   - Frontend server (React)

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Admin Panel: http://localhost:8000/admin/
   - API: http://localhost:8000/api/

### Daily Usage

Just double-click **start-all.bat** to run the application.

To stop the application, either:
- Close the two command windows, OR
- Run **stop-all.bat**

## Script Reference

| Script | Purpose |
|--------|---------|
| `setup-first-time.bat` | **Run once** - Initial setup and configuration |
| `start-all.bat` | **Run daily** - Starts both backend and frontend |
| `start-backend.bat` | Start only the Django backend server |
| `start-frontend.bat` | Start only the React frontend server |
| `stop-all.bat` | Stop all running servers |

## Network Access (Optional)

To access the application from other computers on your network:

1. Find your server's IP address:
   ```powershell
   ipconfig
   ```
   Look for "IPv4 Address" (e.g., 192.168.1.100)

2. Configure Windows Firewall:
   - Allow inbound connections on ports 8000 and 3000

3. Update Django settings:
   - Edit `backend/config/settings.py`
   - Add your server IP to `ALLOWED_HOSTS`:
     ```python
     ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.100']
     ```

4. Update frontend API endpoint:
   - Edit `frontend/src/api/client.ts`
   - Update `API_BASE_URL`:
     ```typescript
     const API_BASE_URL = 'http://192.168.1.100:8000/api';
     ```

5. Access from other computers:
   - Frontend: http://192.168.1.100:3000
   - Admin: http://192.168.1.100:8000/admin/

## Troubleshooting

### Port Already in Use

If you see "port already in use" errors:

```powershell
# Check what's using port 8000
netstat -ano | findstr ":8000"

# Check what's using port 3000
netstat -ano | findstr ":3000"

# Kill the process (replace <PID> with the process ID)
taskkill /PID <PID> /F
```

Or simply run: **stop-all.bat**

### Python Not Found

- Reinstall Python and ensure "Add to PATH" is checked
- Restart your command prompt after installation

### Node/npm Not Found

- Reinstall Node.js
- Restart your command prompt after installation

### Database Errors

Reset the database:

```powershell
cd backend
del db.sqlite3
.venv\Scripts\activate
python manage.py migrate
python manage.py createsuperuser
```

### Frontend Build Errors

Clear node_modules and reinstall:

```powershell
cd frontend
rmdir /s /q node_modules
rmdir /s /q package-lock.json
npm install
```

## Uploading Data

1. Access admin panel: http://localhost:8000/admin/
2. Login with your admin credentials
3. Navigate to **Data Uploads** → **Add Data Upload**
4. Upload your CSV or Excel file
5. Monitor the upload progress
6. View the dashboard at http://localhost:3000

## Backup and Restore

### Manual Backup

Copy the database file:
```powershell
copy backend\db.sqlite3 backend\db.sqlite3.backup
```

### Restore from Backup

```powershell
copy backend\db.sqlite3.backup backend\db.sqlite3
```

## Production Deployment

For production deployment with Docker, see [CLAUDE.md](CLAUDE.md) - Production Deployment section.

## Support

For issues or questions:
- Check [CLAUDE.md](CLAUDE.md) for detailed technical documentation
- Review Django logs in the backend terminal window
- Review React logs in the frontend terminal window
