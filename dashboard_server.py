from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import os
import uvicorn
from client_config_service import ClientConfigService

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration
MASTER_SHEET_URL = os.getenv("MASTER_SHEET_URL", "https://docs.google.com/spreadsheets/d/1zSbn-poFSY512rIPN45a3yhCG7P5sDaXdu_JLoequUI/edit?gid=0#gid=0")
client_service = ClientConfigService(MASTER_SHEET_URL)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        clients = client_service.get_all_clients()
    except Exception as e:
        print(f"Error loading clients: {e}")
        clients = []
    return templates.TemplateResponse("index.html", {"request": request, "clients": clients})

@app.post("/add_client")
async def add_client(
    client_name: str = Form(...),
    search_keywords: str = Form(...),
    report_recipient: str = Form(...),
    sheet_name: str = Form(""),
    sheet_url: str = Form(...)
):
    keyword_list = [k.strip() for k in search_keywords.split(",") if k.strip()]
    
    new_client = {
        "client_id": client_name.lower().replace(" ", "_"),
        "client_name": client_name,
        "search_keywords": keyword_list,
        "report_recipient": report_recipient,
        "sheet_name": sheet_name,
        "sheet_url": sheet_url,
        "parser_settings": {"ignored_emails": []},
        "status": "active"
    }
    
    client_service.save_client(new_client)
    return RedirectResponse(url="/", status_code=303)

@app.get("/edit_client/{client_id}", response_class=HTMLResponse)
async def edit_client_form(request: Request, client_id: str):
    clients = client_service.get_all_clients()
    client = next((c for c in clients if c.get('client_id') == client_id), None)
    if not client:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("edit_client.html", {"request": request, "client": client})

@app.post("/edit_client/{client_id}")
async def edit_client(
    client_id: str,
    client_name: str = Form(...),
    search_keywords: str = Form(...),
    report_recipient: str = Form(...),
    sheet_name: str = Form(""),
    sheet_url: str = Form(...)
):
    # Fetch existing to preserve settings we don't edit here
    clients = client_service.get_all_clients()
    existing = next((c for c in clients if c.get('client_id') == client_id), {})
    
    updated_client = {
        "client_id": client_id,
        "client_name": client_name,
        "search_keywords": [k.strip() for k in search_keywords.split(",") if k.strip()],
        "report_recipient": report_recipient,
        "sheet_name": sheet_name,
        "sheet_url": sheet_url,
        "parser_settings": existing.get("parser_settings", {"ignored_emails": []}),
        "status": existing.get("status", "active")
    }
    
    client_service.save_client(updated_client)
    return RedirectResponse(url="/", status_code=303)

@app.get("/retire_client/{client_id}")
async def retire_client(client_id: str):
    # We need to fetch the full object to re-save it with status=retired
    clients = client_service.get_all_clients()
    client = next((c for c in clients if c.get('client_id') == client_id), None)
    if client:
        client['status'] = 'retired'
        client_service.save_client(client)
        
    return RedirectResponse(url=f"/?action=retired&client_id={client_id}", status_code=303)

@app.get("/restore_client/{client_id}")
async def restore_client(client_id: str):
    clients = client_service.get_all_clients()
    client = next((c for c in clients if c.get('client_id') == client_id), None)
    if client:
        client['status'] = 'active'
        client_service.save_client(client)

    return RedirectResponse(url="/", status_code=303)

@app.get("/delete_client/{client_id}")
async def delete_client(client_id: str):
    # Map delete to retire for safety, or implement hard delete
    client_service.delete_client(client_id)
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Bind to 0.0.0.0 for Cloud Deployment compatibility
    uvicorn.run(app, host="0.0.0.0", port=port)
