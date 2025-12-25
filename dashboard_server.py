from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import os
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CLIENTS_FILE = "clients.json"

def load_clients():
    if not os.path.exists(CLIENTS_FILE):
        return []
    with open(CLIENTS_FILE, "r") as f:
        try:
            val = json.load(f)
            return val if isinstance(val, list) else []
        except:
            return []

def save_clients(clients):
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, indent=4)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    clients = load_clients()
    return templates.TemplateResponse("index.html", {"request": request, "clients": clients})

@app.post("/add_client")
async def add_client(
    client_name: str = Form(...),
    search_keywords: str = Form(...),
    report_recipient: str = Form(...),
    sheet_name: str = Form(""),
    sheet_url: str = Form(...)
):
    clients = load_clients()
    new_client = {
        "client_id": client_name.lower().replace(" ", "_"),
        "client_name": client_name,
        "search_keywords": [k.strip() for k in search_keywords.split(",") if k.strip()],
        "report_recipient": report_recipient,
        "sheet_name": sheet_name,
        "sheet_url": sheet_url,
        "parser_settings": {"ignored_emails": []}
    }
    clients.append(new_client)
    save_clients(clients)
    return RedirectResponse(url="/", status_code=303)

@app.get("/edit_client/{client_id}", response_class=HTMLResponse)
async def edit_client_form(request: Request, client_id: str):
    clients = load_clients()
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
    clients = load_clients()
    for i, c in enumerate(clients):
        if c.get('client_id') == client_id:
            # Update the client, preserving client_id and parser_settings
            clients[i] = {
                "client_id": client_id,  # Keep original ID
                "client_name": client_name,
                "search_keywords": [k.strip() for k in search_keywords.split(",") if k.strip()],
                "report_recipient": report_recipient,
                "sheet_name": sheet_name,
                "sheet_url": sheet_url,
                "parser_settings": c.get("parser_settings", {"ignored_emails": []})
            }
            break
    save_clients(clients)
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete_client/{client_id}")
async def delete_client(client_id: str):
    clients = load_clients()
    clients = [c for c in clients if c.get('client_id') != client_id]
    save_clients(clients)
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
