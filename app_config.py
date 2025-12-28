import os

# Default to Environment Variables (Mock values if not set to avoid crash on import)
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_PASS", "")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")

# Try to load local config.py (overrides env vars if present)
try:
    import config as local_config
    # Only override if the local config has the attribute
    if hasattr(local_config, "GMAIL_USER"): 
        GMAIL_USER = local_config.GMAIL_USER
    if hasattr(local_config, "GMAIL_PASS"): 
        GMAIL_PASS = local_config.GMAIL_PASS
    if hasattr(local_config, "SERVICE_ACCOUNT_FILE"): 
        SERVICE_ACCOUNT_FILE = local_config.SERVICE_ACCOUNT_FILE
except ImportError:
    # config.py doesn't exist (Production/Render environment)
    pass
