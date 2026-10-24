# Client Performance Hub - Lead Agent

Automated lead tracking and performance monitoring agent.

## Features

- Automated lead tracking from email reports
- Google Sheets integration
- Professional HTML Email notifications with performance dashboards
- Multi-client support via Cloud Configuration (Google Sheets)

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up configuration:
   - Copy `config.example.py` to `config.py`
   - Fill in your Gmail credentials and service account path
   - Ensure `MASTER_SHEET_URL` is set in `main.py` or as an environment variable.

3. Run the lead agent:
   ```bash
   # Process leads from the last 2 days
   python main.py --days 2
   ```

## Project Structure

- `main.py` - Lead processing agent entry point
- `client_config_service.py` - Manages client configurations via Google Sheets
- `email_service.py` - Email fetching and sending
- `sheet_service.py` - Individual client Google Sheets integration
- `parsers/` - Email parsers for different lead sources (Forms, Calls, Links)
- `utils.py` - Common utility functions
