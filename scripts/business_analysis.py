import os
from typing import Dict, List, Tuple

import pandas as pd

from config import DATA_PATH
from scripts import data_clean, data_load
from scripts.data_load import SUPPORTED_EXTENSIONS

# Base file name can be overridden to point endpoints to a specific dataset
DEFAULT_BASE_NAME = os.getenv("INVENTORY_BASE_NAME", "inventario")


def load_clean_inventory(base_name: str = DEFAULT_BASE_NAME) -> pd.DataFrame:
    """
    Load and clean the inventory using existing loaders to avoid duplicating logic.
    """
    base_path = DATA_PATH / base_name

    # Permitir que base_name se pase con o sin extensión
    if base_path.suffix.lower() in SUPPORTED_EXTENSIONS:
        actual_path = base_path
    else:
        actual_path = data_load.find_actual_file_path(str(base_path))

    df_raw = data_load.load_data(actual_path)
    return data_clean.data_clean(df_raw)


def _ensure_value_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize numeric columns and ensure valor_total exists for downstream metrics.
    """
    work = df.copy()
    work["cantidad"] = pd.to_numeric(work["cantidad"], errors="coerce").fillna(0)
    work["precio"] = pd.to_numeric(work["precio"], errors="coerce").fillna(0.0)
    if "valor_total" not in work.columns:
        work["valor_total"] = work["cantidad"] * work["precio"]
    work["valor_total"] = pd.to_numeric(work["valor_total"], errors="coerce").fillna(0.0)
    return work


def abc_classification(df: pd.DataFrame) -> Dict[str, object]:
    """
    ABC classification based on contribution to total inventory value.
    A: up to 80% of cumulative value
    B: next 15%
    C: remaining items
    """
    work = _ensure_value_columns(df)
    work = work.sort_values("valor_total", ascending=False).reset_index(drop=True)

    total_valor = work["valor_total"].sum()
    if total_valor <= 0:
        return {"detalle": [], "capital_a_pct": 0.0, "total_valor": 0.0}

    work["participacion"] = work["valor_total"] / total_valor
    work["participacion_acum"] = work["participacion"].cumsum()

    def _asignar_clase(acumulado: float) -> str:
        if acumulado <= 0.80:
            return "A"
        if acumulado <= 0.95:
            return "B"
        return "C"

    work["clase_abc"] = work["participacion_acum"].apply(_asignar_clase)
    capital_a_pct = (
        work.loc[work["clase_abc"] == "A", "valor_total"].sum() / total_valor
    )

    detalle = work[
        [
            "codigo",
            "nombre",
            "categoria",
            "cantidad",
            "precio",
            "valor_total",
            "participacion",
            "participacion_acum",
            "clase_abc",
        ]
    ].to_dict(orient="records")

    return {
        "detalle": detalle,
        "capital_a_pct": round(capital_a_pct * 100, 2),
        "total_valor": round(total_valor, 2),
    }


def _rotation_series(df: pd.DataFrame) -> Tuple[pd.Series, str]:
    """
    Try to infer a rotation/throughput column; fall back to zero to flag immobilized capital.
    """
    candidate_cols = [
        "rotacion",
        "rotacion_mensual",
        "ventas_mensuales",
        "salidas_mensuales",
        "demanda_mensual",
    ]
    for col in candidate_cols:
        if col in df.columns:
            serie = pd.to_numeric(df[col], errors="coerce").fillna(0)
            note = f"Rotacion estimada usando columna '{col}'."
            return serie, note

    serie = pd.Series(0, index=df.index)
    note = (
        "Sin columna de ventas/rotacion; se asume 0 unidades vendidas recientes "
        "para detectar capital inmovilizado (supuesto conservador)."
    )
    return serie, note


def generar_alertas(df: pd.DataFrame, top_n: int = 10) -> Dict[str, object]:
    """
    Produce automatic alerts based on stock percentiles and immobilized capital.
    """
    work = _ensure_value_columns(df)
    if work.empty:
        return {"alertas": [], "umbrales": {}, "supuesto_capital_muerto": ""}

    q25 = work["cantidad"].quantile(0.25)
    q75 = work["cantidad"].quantile(0.75)
    valor_q75 = work["valor_total"].quantile(0.75)
    total_valor = work["valor_total"].sum()

    rotacion, rotacion_nota = _rotation_series(work)
    rotacion_q25 = rotacion.quantile(0.25)

    alertas: List[Dict[str, object]] = []

    def _base_alert(row: pd.Series, tipo: str, detalle: str) -> Dict[str, object]:
        valor = float(row.get("valor_total", 0.0))
        impacto_relativo = (valor / total_valor) if total_valor else 0
        if impacto_relativo >= 0.05:
            severidad = "Alta"
        elif impacto_relativo >= 0.02:
            severidad = "Media"
        else:
            severidad = "Baja"

        return {
            "codigo": row.get("codigo"),
            "nombre": row.get("nombre"),
            "categoria": row.get("categoria"),
            "cantidad": int(row.get("cantidad", 0)),
            "precio": float(row.get("precio", 0.0)),
            "valor_total": valor,
            "impacto_relativo": impacto_relativo,
            "severidad": severidad,
            "tipo": tipo,
            "detalle": detalle,
            "prioridad_valor": float(row.get("valor_total", 0.0)),
            "recomendacion": "Recomendacion: reducir stock gradualmente o revisar rotacion segun contexto.",
        }

    for idx, row in work.iterrows():
        cantidad = row["cantidad"]
        valor = row["valor_total"]
        rot = rotacion.iloc[idx]

        if cantidad > q75:
            alertas.append(
                _base_alert(
                    row,
                    "SOBRE_STOCK",
                    f"Stock {cantidad} > P75 ({q75:.1f}).",
                )
            )

        if cantidad < q25:
            alertas.append(
                _base_alert(
                    row,
                    "RIESGO_QUIEBRE",
                    f"Stock {cantidad} < P25 ({q25:.1f}).",
                )
            )

        if valor >= valor_q75 and rot <= rotacion_q25:
            alertas.append(
                _base_alert(
                    row,
                    "CAPITAL_MUERTO",
                    (
                        f"Valor alto >= P75 ({valor_q75:.2f}) con rotacion baja "
                        f"<= P25 ({rotacion_q25:.2f}). {rotacion_nota}"
                    ),
                )
            )

    alertas = sorted(alertas, key=lambda x: x["prioridad_valor"], reverse=True)[:top_n]

    return {
        "alertas": alertas,
        "umbrales": {
            "stock_p25": q25,
            "stock_p75": q75,
            "valor_p75": valor_q75,
            "rotacion_p25": rotacion_q25,
        },
        "supuesto_capital_muerto": rotacion_nota,
        "total_valor": total_valor,
    }


def simular_what_if(
    df: pd.DataFrame,
    categoria: str,
    porcentaje_reduccion: float,
    top_n: int | None = None,
) -> Dict[str, object]:
    """
    Estimate liberated capital after reducing stock of a category by a percentage.
    Optionally limit the action to the top N items by value in that category.
    """
    work = _ensure_value_columns(df)
    categoria_normalizada = categoria.strip().lower()
    target = work[
        work["categoria"].astype(str).str.strip().str.lower() == categoria_normalizada
    ]

    if target.empty:
        return {
            "categoria": categoria,
            "porcentaje_reduccion": porcentaje_reduccion,
            "capital_liberado": 0.0,
            "valor_actual_categoria": 0.0,
            "valor_estimado_post": 0.0,
            "detalle": [],
            "mensaje": "Categoria no encontrada en el inventario.",
        }

    if top_n and top_n > 0:
        target = target.sort_values("valor_total", ascending=False).head(int(top_n))

    porcentaje = porcentaje_reduccion
    if porcentaje_reduccion > 1:
        porcentaje = porcentaje_reduccion / 100.0
    porcentaje = max(0.0, min(porcentaje, 1.0))

    valor_actual = target["valor_total"].sum()
    capital_liberado = valor_actual * porcentaje
    valor_post = valor_actual - capital_liberado

    detalle = target[
        ["codigo", "nombre", "categoria", "cantidad", "precio", "valor_total"]
    ].to_dict(orient="records")

    return {
        "categoria": categoria,
        "porcentaje_reduccion": round(porcentaje * 100, 2),
        "top_n": int(top_n) if top_n else None,
        "capital_liberado": round(capital_liberado, 2),
        "valor_actual_categoria": round(valor_actual, 2),
        "valor_estimado_post": round(valor_post, 2),
        "detalle": detalle,
    }
