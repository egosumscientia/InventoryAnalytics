import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import DATA_PATH, REPORTS_PATH
from scripts import business_analysis, data_analysis, data_clean, data_load

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".ods"}

app = FastAPI(title="AI Inventory Management")

# Montajes de estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
REPORTS_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_PATH)), name="reports")
templates = Jinja2Templates(directory="templates")


def _load_clean_inventory() -> pd.DataFrame:
    """
    Centraliza la carga/limpieza para reutilizar en los endpoints de analisis.
    """
    try:
        return business_analysis.load_clean_inventory()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - FastAPI maneja la respuesta
        raise HTTPException(
            status_code=500,
            detail=f"Error al preparar datos de inventario: {exc}",
        )


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

    original_name = file.filename or ""
    safe_name = Path(original_name).name  # elimina rutas/../
    ext = Path(safe_name).suffix.lower()

    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida ({ext}). Usa: csv, xlsx u ods.",
        )

    raw_bytes = await file.read()
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="El archivo supera el límite de 20 MB.",
        )

    file_path = DATA_PATH / safe_name
    # Sobrescribe el archivo si ya existía (evita fallar al reintentar)
    with open(file_path, "wb") as f:
        f.write(raw_bytes)

    try:
        df = data_load.load_data(file_path)
        df = data_clean.data_clean(df)
        data_analysis.analizar_inventario(df)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error al procesar el archivo: {exc}")

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
        {"request": request, "filename": safe_name, "summary": summary},
    )


@app.get("/analysis/abc")
def analysis_abc():
    df = _load_clean_inventory()
    return business_analysis.abc_classification(df)


@app.get("/analysis/alerts")
def analysis_alerts(top: int | None = Query(None, ge=1)):
    """
    Devuelve alertas priorizadas. Si no se especifica `top`, se devuelven todas las alertas.
    """
    df = _load_clean_inventory()
    return business_analysis.generar_alertas(df, top_n=top)


@app.get("/analysis/what-if")
def analysis_what_if(
    categoria: str = Query(..., min_length=1),
    porcentaje_reduccion: float = Query(..., gt=0),
    top_n: int | None = Query(None, gt=0, le=1000),
):
    df = _load_clean_inventory()
    return business_analysis.simular_what_if(df, categoria, porcentaje_reduccion, top_n=top_n)
