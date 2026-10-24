import traceback
import time
import json
import os
import socket

# Prevent network calls from hanging indefinitely (e.g. during network dropouts)
socket.setdefaulttimeout(30.0)

import app_config as config
from datetime import datetime
from email_service import EmailService
from sheet_service import SheetService
from client_config_service import ClientConfigService
from parsers.form_parser import FormParser
from parsers.call_parser import CallParser
from parsers.link_parser import LinkReportParser

# Configuration
MASTER_SHEET_URL = os.getenv("MASTER_SHEET_URL") or "https://docs.google.com/spreadsheets/d/1zSbn-poFSY512rIPN45a3yhCG7P5sDaXdu_JLoequUI/edit?gid=0#gid=0"
client_service = ClientConfigService(MASTER_SHEET_URL)

def load_clients():
    try:
        all_clients = client_service.get_all_clients()
        # Only return ACTIVE clients for processing
        return [c for c in all_clients if c.get('status', 'active') == 'active']
    except Exception as e:
        print(f"Error loading clients from Cloud Config: {e}")
        traceback.print_exc()
        return []

def calculate_monthly_stats(existing_data):
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    mtd_total = 0
    mtd_calls = 0
    mtd_forms = 0
    for lead in existing_data:
        lead_date = str(lead.get('Date', ''))
        if lead_date.startswith(current_month):
            mtd_total += 1
            l_type = str(lead.get('Lead Type', '')).lower()
            if 'phone' in l_type: mtd_calls += 1
            elif 'form' in l_type: mtd_forms += 1
    return {'month_name': now.strftime("%B"), 'total': mtd_total, 'calls': mtd_calls, 'forms': mtd_forms}

def generate_html_report(client_name, days_back, leads_to_add, new_calls, new_forms, sheet_url, monthly_stats=None):
    """
    Generates a professional HTML dashboard that adapts to Light/Dark mode.
    """
    leads_html = ""
    for lead in leads_to_add:
        # Determine icon based on type
        lead_type = lead.get('Lead Type', '').lower()
        type_icon = "📞" if "phone" in lead_type else "📄"
        
        contact = lead.get('Phone') or lead.get('Email') or "N/A"
        
        leads_html += f"""
        <tr class="table-row" style="border-bottom: 1px solid #edf2f7;">
            <td style="padding: 15px 10px; color: #718096;" class="text-sub">{lead.get('Date')}</td>
            <td style="padding: 15px 10px; color: #2d3748; font-weight: bold;" class="text-main">{lead.get('Client Name', 'Unknown')}</td>
            <td style="padding: 15px 10px; color: #718096;" class="text-sub">{contact}</td>
            <td style="padding: 15px 10px; color: #718096;" class="text-sub">{type_icon} {lead.get('Lead Type')}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <style>
            @media (prefers-color-scheme: dark) {{
                .body-bg {{ background-color: #1a1a1a !important; color: #ffffff !important; }}
                .container-bg {{ background-color: #222222 !important; border-top: 10px solid #D74E2E !important; }}
                .text-main {{ color: #ffffff !important; }}
                .text-sub {{ color: #bbbbbb !important; }}
                .border-dim {{ border-color: #333 !important; border-top-color: #333 !important; border-bottom-color: #333 !important; border-right-color: #333 !important; }}
                .monthly-box {{ background-color: #2a2a2a !important; border-color: #333 !important; }}
                .table-head {{ background-color: #333 !important; }}
                .table-row {{ border-bottom-color: #444 !important; }}
                .footer-bg {{ background-color: #1a1a1a !important; }}
                .stat-box {{ border-right-color: #333 !important; }}
            }}
        </style>
    </head>
    <body class="body-bg" style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f6; color: #2d3748;">
        <div class="container-bg" style="max-width: 650px; margin: 20px auto; background-color: #ffffff; border-radius: 20px; overflow: hidden; border-top: 10px solid #D74E2E; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
            
            <!-- Header -->
            <div style="padding: 40px 20px 20px; text-align: center;">
                <a href="https://netgain.agency/pal/" style="text-decoration: none; background-color: transparent; display: inline-block;">
                    <img src="cid:logo" width="100" alt="PAL Logo" style="max-width: 100px; height: auto; margin-bottom: 20px; border: 0; background-color: transparent; vertical-align: middle;">
                </a>
                <p class="text-sub" style="margin: 0; color: #718096; font-size: 15px; letter-spacing: 1px;">{client_name} • Lead Performance Update</p>
            </div>

            <hr class="border-dim" style="border: 0; border-top: 1px solid #edf2f7; margin: 0 40px;">

            <!-- Stats Bar -->
            <table style="width: 100%; border-collapse: collapse; margin: 30px 0;">
                <tr>
                    <td class="stat-box" style="width: 33%; text-align: center; border-right: 1px solid #edf2f7;">
                        <div class="text-main" style="font-size: 40px; font-weight: bold; color: #1a202c;">{len(leads_to_add)}</div>
                        <div style="font-size: 12px; color: #D74E2E; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">New Leads</div>
                    </td>
                    <td class="stat-box" style="width: 33%; text-align: center; border-right: 1px solid #edf2f7;">
                        <div class="text-main" style="font-size: 40px; font-weight: bold; color: #1a202c;">{new_calls}</div>
                        <div style="font-size: 12px; color: #D74E2E; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Phone Calls</div>
                    </td>
                    <td style="width: 33%; text-align: center;">
                        <div class="text-main" style="font-size: 40px; font-weight: bold; color: #1a202c;">{new_forms}</div>
                        <div style="font-size: 12px; color: #D74E2E; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Form Submissions</div>
                    </td>
                </tr>
            </table>

            <hr class="border-dim" style="border: 0; border-top: 1px solid #edf2f7; margin: 0 40px;">

            <!-- Content Area -->
            <div style="padding: 30px 40px;">
                <h2 class="text-main" style="margin: 0 0 25px; color: #1a202c; font-size: 20px; font-weight: bold;">Recent Leads Summary</h2>
 
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr class="table-head" style="background-color: #f7fafc; text-align: left;">
                            <th style="padding: 12px; color: #718096; font-size: 12px; text-transform: uppercase;">Date</th>
                            <th style="padding: 12px; color: #718096; font-size: 12px; text-transform: uppercase;">Name</th>
                            <th style="padding: 12px; color: #718096; font-size: 12px; text-transform: uppercase;">Contact</th>
                            <th style="padding: 12px; color: #718096; font-size: 12px; text-transform: uppercase;">Type</th>
                        </tr>
                    </thead>
                    <tbody style="font-size: 14px;">
                        {leads_html}
                    </tbody>
                </table>

                {f'''
                <!-- Monthly Summary Section -->
                <div class="monthly-box" style="background-color: #f8f9fa; border-radius: 12px; padding: 20px; margin-top: 40px; border: 1px solid #e2e8f0;">
                    <h3 class="text-main" style="margin: 0 0 15px; color: #2d3748; font-size: 16px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">{monthly_stats["month_name"]} Overview (MTD)</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td class="text-sub" style="padding: 5px 0; color: #718096; font-size: 14px;">Total Leads this Month:</td>
                            <td style="padding: 5px 0; color: #D74E2E; font-size: 14px; text-align: right; font-weight: bold;">{monthly_stats["total"]}</td>
                        </tr>
                        <tr>
                            <td class="text-sub" style="padding: 5px 0; color: #718096; font-size: 14px;">Monthly Phone Calls:</td>
                            <td class="text-main" style="padding: 5px 0; color: #2d3748; font-size: 14px; text-align: right;">{monthly_stats["calls"]}</td>
                        </tr>
                        <tr>
                            <td class="text-sub" style="padding: 5px 0; color: #718096; font-size: 14px;">Monthly Form Submissions:</td>
                            <td class="text-main" style="padding: 5px 0; color: #2d3748; font-size: 14px; text-align: right;">{monthly_stats["forms"]}</td>
                        </tr>
                    </table>
                </div>
                ''' if monthly_stats else ''}

                <!-- Call to Action -->
                <div style="text-align: center; margin-top: 45px;">
                    <a href="{sheet_url}" 
                       style="display: inline-block; padding: 16px 45px; background-color: #D74E2E; color: #ffffff; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(215, 78, 46, 0.2);">
                       View Full Google Sheet
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <div class="footer-bg" style="padding: 40px 30px; text-align: center; background-color: #1a1a1a; margin-top: 20px;">
                <a href="https://netgain.agency" style="text-decoration: none; background-color: transparent; display: inline-block;">
                    <img src="cid:netgain_logo" width="80" alt="Netgain Logo" style="max-width: 80px; height: auto; margin-bottom: 20px; opacity: 0.8; border: 0; background-color: transparent; vertical-align: middle;">
                </a>
                <p style="margin: 0; color: #555; font-size: 11px; text-transform: uppercase; letter-spacing: 2px;">
                    LEAD AGENT PERFORMANCE • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def process_client(client_config, days_back=1):
    client_name = client_config['client_name']
    print(f"--- Processing Client: {client_name} ---")
    
    email_svc = EmailService(config.GMAIL_USER, config.GMAIL_PASS)
    
    # Prioritize URL over Name for SheetService
    sheet_identifier = client_config.get('sheet_url') or client_config['sheet_name']
    sheet_svc = SheetService(sheet_identifier, config.SERVICE_ACCOUNT_FILE)
    
    parsers = [FormParser(client_config), CallParser(client_config), LinkReportParser(client_config)]
    
    emails = email_svc.fetch_emails(client_config, days=days_back)
    all_leads = []
    for email in emails:
        for parser in parsers:
            try:
                leads = parser.parse(email)
                if leads: all_leads.extend(leads)
            except Exception as e: print(f"Error in {parser.__class__.__name__}: {e}")

    all_leads.sort(key=lambda x: x['Date'])
    
    try:
        sheet_svc.connect()
        existing_data = sheet_svc.get_existing_leads()
        leads_to_add = []
        new_calls = 0
        new_forms = 0
        
        for lead in all_leads:
            if not sheet_svc.lead_exists(lead, existing_data):
                leads_to_add.append(lead)
                existing_data.append(lead)
                l_type = lead.get('Lead Type', '').lower()
                if 'phone' in l_type: new_calls += 1
                elif 'form' in l_type: new_forms += 1
        
        if leads_to_add:
            sheet_svc.append_rows(leads_to_add)
            print(f"Added {len(leads_to_add)} leads.")
        
        monthly_stats = calculate_monthly_stats(existing_data)
        subject = f"Lead Agent Update: {client_name} - {len(leads_to_add)} New Leads"
        html_body = generate_html_report(client_name, days_back, leads_to_add, new_calls, new_forms, client_config.get('sheet_url', '#'), monthly_stats)
        logos = {
            'logo': 'pal_logo.png',
            'netgain_logo': 'netgain_logo.png'
        }
        email_svc.send_notification_email(subject, html_body, client_config['report_recipient'], is_html=True, logos=logos)
        
    except Exception as e:
        print(f"Error processing {client_name}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=2)
    args = parser.parse_args()

    clients = load_clients()
    for client in clients:
        process_client(client, days_back=args.days)
    print("All clients processed.")
