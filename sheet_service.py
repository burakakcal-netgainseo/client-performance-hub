import gspread
from google.oauth2.service_account import Credentials
import app_config as config
import time
import traceback

class SheetService:
    def __init__(self, sheet_identifier, creds_file):
        """
        sheet_identifier can be a Sheet Name or a full Google Sheet URL.
        """
        self.scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds_file = creds_file
        self.sheet_identifier = sheet_identifier
        self.headers = ['Date', 'Client Name', 'Email', 'Phone', 'Platform', 'Lead Type', 'Sold?', 'Forecasted Revenue', 'Notes']
        self.client = None
        self.sheet = None

    def connect(self):
        try:
            print(f"Connecting to Google Sheets using {self.creds_file}...")
            creds = Credentials.from_service_account_file(self.creds_file, scopes=self.scope)
            self.client = gspread.authorize(creds)
            
            # Open the spreadsheet
            if "docs.google.com/spreadsheets" in self.sheet_identifier:
                print(f"Opening sheet by URL...")
                self.sheet = self.client.open_by_url(self.sheet_identifier).sheet1
            else:
                print(f"Opening sheet by name '{self.sheet_identifier}'...")
                self.sheet = self.client.open(self.sheet_identifier).sheet1
            
            # Verify/Update headers
            current_headers = self.sheet.row_values(1)
            if not current_headers:
                print("Sheet is empty. Adding headers...")
                self.sheet.append_row(self.headers)
            elif current_headers != self.headers:
                print(f"Warning: Sheet headers {current_headers} might not match expected {self.headers}.")
        
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"\n[ERROR] Could not find Google Sheet '{self.sheet_name}'.")
            raise

        except gspread.exceptions.APIError as e:
            if "Google Sheets API has not been used" in str(e) or "disabled" in str(e):
                print(f"\n[ERROR] Google Sheets API is not enabled for this project.")
                print(f"PLEASE FIX: Click the link below to enable it:")
                # Attempt to extract link or just give general advice
                print(f"   https://console.developers.google.com/apis/api/sheets.googleapis.com/overview")
                print("   Then wait 1-2 minutes and try code again.\n")
            raise e

        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            raise e

    def get_existing_leads(self):
        if not self.sheet:
            self.connect()
        return self.sheet.get_all_records()

    def lead_exists(self, new_lead, existing_leads):
        new_date = str(new_lead.get('Date', '')).strip()
        new_phone = str(new_lead.get('Phone', '')).strip()
        new_email = str(new_lead.get('Email', '')).strip()
        new_name = str(new_lead.get('Client Name', '')).strip().lower()
        
        generic_names = ['wireless caller', 'unknown caller', 'unknown', 'anonymous', 'private number', 'restricted', 'spam? meta', 'robo? meta']
        
        for lead in existing_leads:
            if lead == self.headers: continue
                
            ex_date = str(lead.get('Date', '')).strip()
            ex_phone = str(lead.get('Phone', '')).strip()
            ex_email = str(lead.get('Email', '')).strip()
            ex_name = str(lead.get('Client Name', '')).strip().lower()
            
            if new_date != ex_date: continue
                
            if (new_phone and new_phone == ex_phone) or (new_email and new_email == ex_email):
                return True
                
            if new_name and new_name == ex_name:
                if any(g in new_name for g in generic_names):
                    continue
                return True
        return False

    def add_row(self, row_data):
        if not self.sheet: self.connect()
        if isinstance(row_data, dict):
            row = [row_data.get(h, "") for h in self.headers]
        else:
            row = row_data
        self.sheet.append_row(row)

    def insert_rows(self, rows_list_of_dicts):
        """
        Bulk insert rows at the top (row 2) to maintain Descending Order.
        """
        if not self.sheet:
            self.connect()
            
        if not rows_list_of_dicts:
            return

        # Convert all dicts to list-of-lists following header order
        rows_to_insert = []
        for r_data in rows_list_of_dicts:
            row = [r_data.get(h, "") for h in self.headers]
            rows_to_insert.append(row)
            
        try:
            print(f"Inserting {len(rows_to_insert)} rows at the top of the sheet...")
            self.sheet.insert_rows(rows_to_insert, row=2)
            print("Bulk insert complete.")
        except Exception as e:
            print(f"Error inserting rows: {e}")
            traceback.print_exc()
            raise e

    def append_rows(self, rows_list_of_dicts):
        if not self.sheet: self.connect()
        if not rows_list_of_dicts: return
        rows_to_append = [[r_data.get(h, "") for h in self.headers] for r_data in rows_list_of_dicts]
        try:
            print(f"Appending {len(rows_to_append)} rows...")
            self.sheet.append_rows(rows_to_append)
        except Exception as e:
            print(f"Error appending rows: {e}")
            raise e
