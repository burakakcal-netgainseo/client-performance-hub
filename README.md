# Client Performance Hub

A performance monitoring dashboard for tracking client leads and performance metrics.

## Features

- Client onboarding and management
- Automated lead tracking from email reports
- Google Sheets integration
- Email notifications with performance dashboards
- Multi-client support

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up configuration:
   - Copy `config.example.py` to `config.py`
   - Fill in your Gmail credentials and service account path

3. Run the dashboard:
   ```bash
   python dashboard_server.py
   ```

4. Access at: `http://localhost:8000`

## Deployment

This application is configured for deployment on Railway.app or similar platforms.

### Environment Variables (Set in Railway Dashboard)

- `PORT` - Automatically set by Railway
- Add your Gmail credentials and service account JSON as environment variables if needed

## Project Structure

- `dashboard_server.py` - FastAPI web server
- `main.py` - Lead processing agent
- `email_service.py` - Email handling
- `sheet_service.py` - Google Sheets integration
- `templates/` - HTML templates
- `static/` - Static assets (logos, CSS)
- `parsers/` - Email parsers for different lead sources
