import json
import os
from client_config_service import ClientConfigService

# Configuration
MASTER_SHEET_URL = "https://docs.google.com/spreadsheets/d/1zSbn-poFSY512rIPN45a3yhCG7P5sDaXdu_JLoequUI/edit?gid=0#gid=0"
CLIENTS_FILE = "clients.json"

def migrate():
    print("Starting migration...")
    
    if not os.path.exists(CLIENTS_FILE):
        print("No clients.json found. Skipping migration.")
        return

    # Load local clients
    with open(CLIENTS_FILE, 'r') as f:
        local_clients = json.load(f)
    print(f"Found {len(local_clients)} clients in clients.json")

    # Connect to service
    service = ClientConfigService(MASTER_SHEET_URL)
    service.connect() # Verify connection before loop
    
    # Save each client to sheet
    for client in local_clients:
        print(f"Migrating {client.get('client_name')}...")
        service.save_client(client)
        
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
