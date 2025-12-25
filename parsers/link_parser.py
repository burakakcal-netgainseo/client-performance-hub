import re
import requests
import pandas as pd
import io
# import config  # Removed hardcoded config
from .base import BaseParser
from bs4 import BeautifulSoup
import traceback
from utils import format_name, format_phone

class LinkReportParser(BaseParser):
    def parse(self, email_msg):
        # 1. Sender Check (Safety net)
        # If it's from CTM, we trust it even if subject varies slightly
        sender = email_msg.from_ or ""
        is_ctm_sender = "calltrackingmetrics.com" in sender.lower()

        # 2. Subject Check
        subject = email_msg.subject.lower()
        client_name = self.client_config.get('client_name', '').lower()
        is_correct_subject = "call log export" in subject and client_name in subject
        
        # If neither matches, skip
        if not is_ctm_sender and not is_correct_subject:
             return []

        html_body = email_msg.html
        if not html_body:
            return []
            
        soup = BeautifulSoup(html_body, 'html.parser')
        links = soup.find_all('a', href=True)
        
        results = []
        
        print(f"DEBUG: LinkParser checking '{email_msg.subject}'. Found {len(links)} links.")
        
        for link in links:
            href = link['href']
            text = link.get_text().lower()
            
            # heuristic to find the report link
            # look for 'csv', 'download', 'report', 'calllog' in url or text
            if ('csv' in href.lower() or 'download' in href.lower() or 'calllog' in href.lower() or
                'csv' in text or 'download' in text or 'view report' in text):
                
                print(f"DEBUG: Found potential report link: {href}")
                
                try:
                    # Download the content with User-Agent to avoid blocking
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(href, headers=headers)
                    response.raise_for_status()
                    
                    content_type = response.headers.get('Content-Type', '').lower()
                    url_lower = href.lower()
                    
                    df = None
                    
                    # Check for Excel (.xls, .xlsx)
                    # Check for Excel (.xls, .xlsx)
                    if 'excel' in content_type or 'spreadsheet' in content_type or '.xls' in url_lower:
                        print(f"DEBUG: Detected Excel format for {href}")
                        try:
                            # Read without header first to look for the real header row
                            # (Many reports have metadata in first few rows)
                            df_raw = pd.read_excel(io.BytesIO(response.content), header=None)
                            
                            header_idx = -1
                            # Scan first 20 rows for "Date" and ("Phone" or "Caller" or "Source")
                            for i, row in df_raw.head(20).iterrows():
                                row_vals = [str(v).lower() for v in row.values]
                                if any('date' in v for v in row_vals) and \
                                   (any('phone' in v for v in row_vals) or any('caller' in v for v in row_vals) or any('source' in v for v in row_vals)):
                                    header_idx = i
                                    print(f"DEBUG: Found header at row {i}: {row_vals}")
                                    break
                            
                            if header_idx != -1:
                                # Set new header
                                df = df_raw.iloc[header_idx+1:].copy()
                                df.columns = df_raw.iloc[header_idx]
                            else:
                                # Fallback: Assume row 0 is header
                                df = pd.read_excel(io.BytesIO(response.content))
                                
                        except Exception as excel_err:
                            print(f"DEBUG: Failed to parse as Excel: {excel_err}. Trying CSV fallback...")
                            # Fallback
                            try:
                                df = pd.read_csv(io.BytesIO(response.content))
                            except:
                                pass
                                
                    # Check for CSV
                    elif 'csv' in content_type or '.csv' in url_lower or 'text' in content_type:
                        df = pd.read_csv(io.BytesIO(response.content))
                        
                    if df is None:
                        print(f"DEBUG: Could not determine format for {href} (Type: {content_type})")
                        continue
                        
                    # Normalize columns
                    df.columns = [str(c).lower().strip() for c in df.columns]
                    print(f"DEBUG: Downloaded Data with columns: {list(df.columns)}")
                        
                    # Find Phone Column - Prioritize "Customer #" (User specified) or "Caller Number"
                    phone_col = None
                    
                    # 1. Look for explicit "Customer #"
                    pk_candidates = [c for c in df.columns if 'customer' in c and '#' in c]
                    if pk_candidates:
                        phone_col = pk_candidates[0]
                        print(f"DEBUG: Found Phone Column (Customer #): {phone_col}")
                    
                    # 2. Look for "Caller Number"
                    if not phone_col:
                         candidates = [c for c in df.columns if 'caller' in c and 'number' in c]
                         if candidates:
                             phone_col = candidates[0]
                         
                    # 3. Fallback
                    if not phone_col:
                        phone_col = next((c for c in df.columns if 'phone' in c or 'source' in c or 'caller' in c or 'number' in c), None)
                    
                    # Find Date/Time column
                    # User specified Column S (19th column, index 18)
                    date_col = None
                    if len(df.columns) >= 19:
                         date_col = df.columns[18]
                         print(f"DEBUG: Using Column S (Index 18) for Date/Time: {date_col}")
                    
                    if not date_col:
                        # Fallback: Common names
                        date_col = next((c for c in df.columns if 'date' in c or 'start' in c or 'time' in c), None)
                    
                    if not phone_col:
                        print("DEBUG: No phone column found in downloaded CSV.")
                        continue
                        
                    client_name_lower = self.client_config.get('client_name', '').lower()
                    
                    for _, row in df.iterrows():
                        # naive check: is client name in the row?
                        row_str = row.astype(str).str.lower().str.cat(sep=' ')
                        
                        if client_name_lower in row_str or client_name_lower in subject:
                            phone = str(row[phone_col])
                            
                            # Extract Date from row if column exists, else email date
                            lead_date = email_msg.date.strftime("%Y-%m-%d")
                            if date_col:
                                    try:
                                        # Parse date from CSV string
                                        row_date_val = str(row[date_col])
                                        
                                        # Check against nan/nat
                                        if row_date_val.lower() == 'nan' or row_date_val.lower() == 'nat':
                                            row_date_val = ""
                                            
                                        if row_date_val:
                                            # Try to split if it contains time '2025-12-20 08:30:00'
                                            if ' ' in row_date_val:
                                                row_date_val = row_date_val.split(' ')[0]
                                            lead_date = row_date_val
                                    except:
                                        pass
                            
                            # Extract Name if available, else Unknown
                            lead_name = "Unknown"
                            name_col = next((c for c in df.columns if 'name' in c or 'customer' in c), None)
                            if name_col:
                                 lead_name = str(row[name_col])
    
                            # --- SPAM FILTER ---
                            if lead_name:
                                ln_lower = lead_name.lower()
                                if "robo" in ln_lower or "spam" in ln_lower:
                                    print(f"DEBUG: Skipping Spam/Robo Call: {lead_name}")
                                    continue
                            # -------------------

                            # --- PHONE VALIDATION ---
                            # User requirement: All call leads MUST have a phone number.
                            if not phone:
                                # Try one last ditch: name might be the phone number in some CTM exports?
                                # But safer to skip to avoid bad data.
                                # print("DEBUG: Skipping row with no phone number.")
                                continue
                            # ------------------------

                            # --- FIELD EXTRACTION ---
                            # Extract other useful fields into Notes
                            notes_parts = []
                            
                            # CTM 'notes' column
                            if 'notes' in row and str(row['notes']).lower() != 'nan':
                                notes_parts.append(f"Notes: {row['notes']}")
                                
                            # CTM 'tracking source' or 'source'
                            src = ""
                            if 'tracking source' in row and str(row['tracking source']).lower() != 'nan':
                                src = str(row['tracking source'])
                            elif 'source' in row and str(row['source']).lower() != 'nan':
                                src = str(row['source'])
                                
                            if src:
                                notes_parts.append(f"Source: {src}")
                                
                            # CTM 'campaign'
                            if 'campaign' in row and str(row['campaign']).lower() != 'nan':
                                notes_parts.append(f"Campaign: {row['campaign']}")
                                
                            # CTM 'keyword'
                            if 'keyword' in row and str(row['keyword']).lower() != 'nan':
                                notes_parts.append(f"Keyword: {row['keyword']}")
                                
                            final_notes = " | ".join(notes_parts)
                            # ------------------------

                            results.append({
                                'Date': lead_date,
                                'Client Name': format_name(lead_name),
                                'Email': '',
                                'Phone': format_phone(phone),
                                'Platform': 'CallTrackingMetrics',
                                'Lead Type': 'Phone Call', 
                                'Sold?': '',
                                'Forecasted Revenue': '',
                                'Notes': final_notes
                            })
                                
                except Exception as e:
                    print(f"Error processing link {href}: {e}")
                    # traceback.print_exc()
        
        return results
