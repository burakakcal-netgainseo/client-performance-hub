import pandas as pd
import io
# import config  # Removed hardcoded config
from .base import BaseParser
from utils import format_name, format_phone

class CallParser(BaseParser):
    def parse(self, email_msg):
        results = []
        for att in email_msg.attachments:
            if att.filename.lower().endswith('.csv'):
                try:
                    # Load CSV content
                    csv_content = att.payload
                    # If payload is bytes, decode it
                    if isinstance(csv_content, str):
                         csv_content = csv_content.encode('utf-8')
                    
                    df = pd.read_csv(io.BytesIO(csv_content))
                    
                    # Normalize headers to lowercase for easier matching
                    df.columns = [c.lower() for c in df.columns]
                    
                    # Look for client column if it exists to filter specific client
                    client_name_lower = self.client_config.get('client_name', '').lower()
                    
                    # Identify relevant columns (heuristic mapping)
                    # We look for 'caller', 'source', 'duration', 'phone'
                    phone_col = None
                    
                    # 1. Look for explicit "Customer #"
                    pk_candidates = [c for c in df.columns if 'customer' in c and '#' in c]
                    if pk_candidates:
                        phone_col = pk_candidates[0]
                    
                    # 2. Look for "Caller Number"
                    if not phone_col:
                        candidates = [c for c in df.columns if 'caller' in c and 'number' in c]
                        if candidates:
                            phone_col = candidates[0]
                            
                    # 3. Fallback
                    if not phone_col:
                         phone_col = next((c for c in df.columns if 'phone' in c.lower() or 'source' in c.lower() or 'caller' in c.lower()), None)
                    
                    name_col = next((c for c in df.columns if 'name' in c or 'customer' in c), None)
                    date_col = next((c for c in df.columns if 'date' in c or 'start' in c or 'time' in c), None)
                    
                    if not phone_col:
                        continue # Can't identify leads without phone/caller ID
                        
                    for _, row in df.iterrows():
                        # Check if this row belongs to the client
                        # We convert entire row to string to search for client name
                        row_str = row.astype(str).str.lower().str.cat(sep=' ')
                        if client_name_lower in row_str:
                            
                            phone = str(row[phone_col])
                            
                            # --- PHONE VALIDATION ---
                            # Skip if empty/nan
                            if not phone or str(phone).lower() == 'nan':
                                continue
                            # ------------------------
                            
                            # Name is tricky in call reports, often just Caller ID or empty
                            name = str(row[name_col]) if name_col else "Unknown Caller"
                            
                            # Extract Date from row
                            lead_date = email_msg.date.strftime("%Y-%m-%d")
                            if date_col:
                                try:
                                    row_date_val = str(row[date_col])
                                    if row_date_val.lower() == 'nan' or row_date_val.lower() == 'nat':
                                        row_date_val = ""

                                    if row_date_val:
                                        if ' ' in row_date_val:
                                            row_date_val = row_date_val.split(' ')[0]
                                        lead_date = row_date_val
                                except:
                                    pass
                            
                            # --- SPAM FILTER ---
                            if name:
                                ln_lower = str(name).lower()
                                if "robo" in ln_lower or "spam" in ln_lower:
                                    # print(f"DEBUG: Skipping Spam/Robo Call in Attachment: {name}")
                                    continue
                            # -------------------

                            results.append({
                                'Date': lead_date,
                                'Client Name': format_name(name),
                                'Email': '', # Usually no email in call reports
                                'Phone': format_phone(phone),
                                'Platform': 'Call Tracking',
                                'Lead Type': 'Phone Call',
                                'Sold?': '',
                                'Forecasted Revenue': '',
                                'Notes': ''
                            })
                            
                except Exception as e:
                    print(f"Error parsing CSV attachment {att.filename}: {e}")
                    
        return results
