import gspread
from google.oauth2.service_account import Credentials
import json
import os
from sheet_service import SheetService

class ClientConfigService:
    def __init__(self, master_sheet_url, creds_file="service_account.json"):
        self.master_sheet_url = master_sheet_url
        self.creds_file = creds_file
        self.client = None
        self.sheet = None
        # Columns in the Config Sheet
        self.headers = [
            "client_id", "client_name", "status", "report_recipient", 
            "sheet_url", "sheet_name", "search_keywords", "parser_settings"
        ]

    def connect(self):
        if not self.client:
            # Re-use the logic from SheetService or standard gspread auth
            # For Render compatibility, we might need to load creds from ENV later, 
            # but for now we rely on the file existing (or being created from ENV).
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Check if we need to load from ENV (Render support)
            if not os.path.exists(self.creds_file) and os.getenv("GOOGLE_CREDENTIALS_JSON"):
                print("Loading credentials from Environment Variable...")
                with open(self.creds_file, "w") as f:
                    f.write(os.getenv("GOOGLE_CREDENTIALS_JSON"))
            
            creds = Credentials.from_service_account_file(self.creds_file, scopes=scope)
            self.client = gspread.authorize(creds)
            print(f"Connecting to Master Config Sheet: {self.master_sheet_url}")
            self.sheet = self.client.open_by_url(self.master_sheet_url).sheet1
            
            # Initialize headers if empty
            if not self.sheet.row_values(1):
                self.sheet.append_row(self.headers)

    def get_all_clients(self):
        self.connect()
        records = self.sheet.get_all_records()
        clients = []
        for r in records:
            # Parse JSON fields
            try:
                keywords = json.loads(r.get('search_keywords', '[]'))
            except:
                keywords = [k.strip() for k in str(r.get('search_keywords', '')).split(',')]
            
            try:
                parser_settings = json.loads(r.get('parser_settings', '{}'))
            except:
                parser_settings = {}

            client = {
                "client_id": r.get('client_id'),
                "client_name": r.get('client_name'),
                "status": r.get('status', 'active'),
                "report_recipient": r.get('report_recipient'),
                "sheet_url": r.get('sheet_url'),
                "sheet_name": r.get('sheet_name'),
                "search_keywords": keywords,
                "parser_settings": parser_settings
            }
            clients.append(client)
        return clients

    def save_client(self, client_dict):
        """Adds a new client or updates an existing one"""
        self.connect()
        
        # Prepare row data
        row_data = [
            client_dict.get('client_id'),
            client_dict.get('client_name'),
            client_dict.get('status', 'active'),
            client_dict.get('report_recipient'),
            client_dict.get('sheet_url'),
            client_dict.get('sheet_name'),
            json.dumps(client_dict.get('search_keywords', [])),
            json.dumps(client_dict.get('parser_settings', {}))
        ]

        # Check if exists
        cell = None
        try:
            cell = self.sheet.find(client_dict.get('client_id'), in_column=1)
        except gspread.exceptions.CellNotFound:
            pass

        if cell:
            # Update existing row
            # gspread uses 1-based indexing. cell.row is the row number.
            # We update the specific range for that row.
            # Convert row_data to cells? Or just update cells loop.
            # update_cell is slow if looped. update(range, [row_data]) is better.
            
            # Let's just re-write the row
            # Range: A{row}:H{row}
            range_name = f"A{cell.row}:H{cell.row}"
            self.sheet.update(range_name=range_name, values=[row_data])
        else:
            # Append new
            self.sheet.append_row(row_data)
            
    def delete_client(self, client_id):
        # We prefer soft delete (status=retired) via save_client, but if hard delete needed:
        self.connect()
        try:
            cell = self.sheet.find(client_id, in_column=1)
            self.sheet.delete_rows(cell.row)
        except:
            pass
