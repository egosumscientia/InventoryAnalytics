# InventoryManager

FastAPI (UI web) para limpiar y analizar inventarios (CSV/XLSX/ODS), generar KPIs y gráficos.

## Rutas configurables
- Datos: `INVENTORY_DATA_PATH` (por defecto `data/` en la raíz del proyecto).
- Reportes/gráficos: `INVENTORY_REPORTS_PATH` (por defecto `reports/` en la raíz).
- Nombre base del archivo: `INVENTORY_BASE_NAME` (por defecto `inventario`).

## Uso web (FastAPI)
1. Instala dependencias: `pip install -r requirements.txt`
2. Arranca el servidor: `uvicorn server:app --reload`
3. UI:
   - `/` dashboard (KPIs + gráficos generados)
   - `/upload` para subir archivo, limpiar, analizar y actualizar KPIs/gráficos.

## Salidas generadas
- `reports/valor_categoria_real.png` y `reports/stock_analizado_confiable.png`
- `reports/latest_summary.json` (últimos KPIs) y `reports/latest_run.txt` (gráficos disponibles)
