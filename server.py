import json

import pandas as pd
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import DATA_PATH, REPORTS_PATH
from scripts import data_analysis, data_clean, data_load

app = FastAPI(title="AI Inventory Management")

# Montajes de estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
REPORTS_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_PATH)), name="reports")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    charts = [p.name for p in REPORTS_PATH.glob("*.png")] if REPORTS_PATH.exists() else []

    summary_file = REPORTS_PATH / "latest_summary.json"
    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
    else:
        summary = {
            "Total Productos": 0,
            "Categorías": 0,
            "Stock Promedio": 0,
            "Valor Total": "$0",
        }

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "summary": summary, "charts": charts},
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile):
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    file_path = DATA_PATH / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Procesamiento
    df = data_load.load_data(file_path)
    df = data_clean.data_clean(df)
    data_analysis.analizar_inventario(df)

    charts = [p.name for p in REPORTS_PATH.glob("*.png")]

    summary = {
        "Total Productos": len(df),
        "Categorías": df["categoria"].nunique(),
        "Stock Promedio": round(df["cantidad"].mean(), 2),
        "Valor Total": f"${df['valor_total'].sum():,.2f}",
    }

    # Persistencia de últimos resultados
    latest_run_path = REPORTS_PATH / "latest_run.txt"
    with open(latest_run_path, "w", encoding="utf-8") as f:
        f.write(str(charts))

    latest_summary = summary
    with open(REPORTS_PATH / "latest_summary.json", "w", encoding="utf-8") as f:
        json.dump(latest_summary, f, ensure_ascii=False, indent=2)

    return templates.TemplateResponse(
        "results.html",
        {"request": request, "filename": file.filename, "summary": summary},
    )
