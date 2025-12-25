# InventoryManager

FastAPI web UI to clean and analyze inventory files (CSV/XLSX/ODS), generate KPIs/charts, and expose actionable analytics.

## Features
- Upload, clean, and normalize inventory data (codigo, nombre, categoria, ubicacion, cantidad, precio, valor_total).
- Charts auto-generated: stock distribution and value by category (saved to `reports/`).
- ABC classification by inventory value (% capital en clase A).
- Alerts with severity (Alta/Media/Baja) for sobre stock, riesgo de quiebre, y capital muerto; sorted by economic impact with recommendations.
- What-if simulator: estimate capital liberado por categoria, con opcion de limitar a top N items.
- Dashboard UI shows KPIs, charts, ABC, alert list (filter/pagination), what-if form with instant preview, and KPI de Capital en Riesgo.

## Configurable paths
- Datos: `INVENTORY_DATA_PATH` (default `data/`).
- Reportes/graficos: `INVENTORY_REPORTS_PATH` (default `reports/`).
- Nombre base del archivo: `INVENTORY_BASE_NAME` (default `inventario`).

## How to run (dev)
1) Install deps: `pip install -r requirements.txt`
2) Start server: `uvicorn server:app --reload`
3) Open UI: http://localhost:8000/
   - Dashboard (KPIs, charts, ABC, Capital en Riesgo, alertas, what-if)
   - Upload page: `/upload`

## API (JSON)
- `GET /analysis/abc` -> ABC classes + `% capital` en clase A (includes total_valor y detalle).
- `GET /analysis/alerts?top=50` -> alertas priorizadas con severidad, recomendacion y umbrales.
- `GET /analysis/what-if?categoria=...&porcentaje_reduccion=...&top_n=` -> capital liberado estimado (no persiste cambios).

## Outputs generated
- Charts: `reports/valor_categoria_real.png`, `reports/stock_analizado_confiable.png`
- Latest KPIs/summary: `reports/latest_summary.json`
- Latest run charts list: `reports/latest_run.txt`

## Notes
- What-if preview en el dashboard usa datos cargados (no modifica archivos ni requiere endpoint nuevo).
- Capital en Riesgo (%) = suma(valor_alertas) / valor_total * 100, calculado en el front usando alertas actuales.
