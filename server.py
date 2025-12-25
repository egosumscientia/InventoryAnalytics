from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from scripts import data_analysis, data_clean, data_load
import pandas as pd
import os

app = FastAPI(title="AI Inventory Management")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")
templates = Jinja2Templates(directory="templates")

DATA_PATH = "data"
REPORTS_PATH = "reports"


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    # Cargar solo los archivos PNG del directorio reports
    charts = []
    if os.path.exists(REPORTS_PATH):
        charts = [f for f in os.listdir(
            REPORTS_PATH) if f.lower().endswith(".png")]

    # Intentar leer el último resumen guardado
    summary_file = os.path.join(REPORTS_PATH, "latest_summary.json")
    if os.path.exists(summary_file):
        import json
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
    else:
        summary = {"Total Productos": 0, "Categorías": 0,
                   "Stock Promedio": 0, "Valor Total": "$0"}

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "summary": summary, "charts": charts}
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile):
    os.makedirs(DATA_PATH, exist_ok=True)
    file_path = f"{DATA_PATH}/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # --- Reutiliza tu backend real ---
    df = data_load.load_data(file_path)
    df = data_clean.data_clean(df)
    data_analysis.analizar_inventario(df)

    # Guarda nombres de gráficos generados
    charts = [f for f in os.listdir(REPORTS_PATH) if f.endswith(".png")]

    # Persistencia del último resumen
    latest_path = os.path.join(REPORTS_PATH, "latest_run.txt")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(str(charts))

    # Calcula resumen rápido
    summary = {
        "Total Productos": len(df),
        "Categorías": df["categoria"].nunique(),
        "Stock Promedio": round(df["cantidad"].mean(), 2),
        "Valor Total": f"${df['valor_total'].sum():,.2f}"
    }

    import json

    # Guarda KPIs en reports/latest_summary.json
    latest_summary = {
        "Total Productos": len(df),
        "Categorías": df["categoria"].nunique(),
        "Stock Promedio": round(df["cantidad"].mean(), 2),
        "Valor Total": f"${df['valor_total'].sum():,.2f}"
    }

    os.makedirs(REPORTS_PATH, exist_ok=True)
    with open(os.path.join(REPORTS_PATH, "latest_summary.json"), "w", encoding="utf-8") as f:
        json.dump(latest_summary, f, ensure_ascii=False, indent=2)

    return templates.TemplateResponse("results.html", {
        "request": request,
        "filename": file.filename,
        "summary": summary
    })
