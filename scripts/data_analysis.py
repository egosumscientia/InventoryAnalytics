from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from config import REPORTS_PATH


def analizar_inventario(df: pd.DataFrame) -> None:
    """
    Análisis principal para columnas:
    codigo, nombre, cantidad, precio, categoria, ubicacion, valor_total
    """
    print("\n=== ANÁLISIS AVANZADO DE INVENTARIO ===")

    # --- Análisis de Stock ---
    print("\n--- Análisis de Stock ---")
    stock_bajo(df, umbral=10)
    stock_excesivo(df, umbral=100)
    promedio_stock_categoria(df)
    productos_sin_stock(df)

    # --- Análisis Económico ---
    print("\n--- Análisis Económico ---")
    valor_total_categoria(df)
    productos_mas_costosos(df, n=5)
    valor_min_max(df)

    # --- Visualizaciones ---
    print("\n--- Visualizaciones ---")
    grafico_distribucion_stock(df)
    grafico_valor_categoria(df)


# ========== FUNCIONES DE ANÁLISIS ==========
def stock_bajo(df: pd.DataFrame, umbral: int) -> None:
    bajo = df[df["cantidad"] < umbral][["codigo", "nombre", "cantidad"]]
    print(f"\nProductos con menos de {umbral} unidades (stock bajo):")
    print(bajo.to_string(index=False))


def stock_excesivo(df: pd.DataFrame, umbral: int) -> None:
    excesivo = df[df["cantidad"] > umbral][["codigo", "nombre", "cantidad"]]
    print(f"\nProductos con más de {umbral} unidades (stock excesivo):")
    print(excesivo.to_string(index=False))


def promedio_stock_categoria(df: pd.DataFrame) -> None:
    promedio = df.groupby("categoria")["cantidad"].mean().round(1)
    print("\nPromedio de unidades por categoría:")
    print(promedio.to_string())


def productos_sin_stock(df: pd.DataFrame) -> None:
    sin_stock = df[df["cantidad"] == 0][["codigo", "nombre"]]
    if not sin_stock.empty:
        print("\n¡ALERTA! Productos agotados:")
        print(sin_stock.to_string(index=False))
    else:
        print("\nNo hay productos agotados en el inventario.")


def valor_total_categoria(df: pd.DataFrame) -> None:
    if "valor_total" not in df.columns:
        df["valor_total"] = df["cantidad"] * df["precio"]
    total = df.groupby("categoria")["valor_total"].sum()
    print("\nValor total del inventario por categoría:")
    print(total.to_string())


def productos_mas_costosos(df: pd.DataFrame, n: int) -> None:
    costosos = df.nlargest(n, "precio")[["codigo", "nombre", "precio"]]
    print(f"\nTop {n} productos más costosos:")
    print(costosos.to_string(index=False))


def valor_min_max(df: pd.DataFrame) -> None:
    min_valor = df.loc[df["precio"].idxmin()][["codigo", "nombre", "precio"]]
    max_valor = df.loc[df["precio"].idxmax()][["codigo", "nombre", "precio"]]
    print("\nProducto más económico:")
    print(min_valor.to_string())
    print("\nProducto más costoso:")
    print(max_valor.to_string())


# ========== VISUALIZACIONES ==========
def grafico_distribucion_stock(df: pd.DataFrame) -> None:
    """
    Histograma de distribución de stock con configuración auto-contenida.
    """
    plt.figure(figsize=(12, 7), dpi=120, facecolor="white")

    # Limpieza de datos robusta
    df = df.copy()
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
    datos = df[df["cantidad"].notna() & (df["cantidad"] >= 0)]["cantidad"]

    # Configuración manual de estilo
    plt.rcParams.update(
        {
            "axes.facecolor": "white",
            "axes.edgecolor": "0.3",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": ":",
            "font.family": "sans-serif",
        }
    )

    # Histograma
    n_bins = min(15, len(datos.unique()))
    plt.hist(
        datos,
        bins=n_bins,
        color="#3498db",
        edgecolor="#ecf0f1",
        alpha=0.85,
        linewidth=1.5,
    )

    # Líneas de referencia
    mediana = datos.median()
    q75 = datos.quantile(0.75)

    plt.axvline(
        mediana,
        color="#e74c3c",
        linestyle="--",
        linewidth=1.5,
        label=f"Mediana ({mediana:.0f} uds)",
    )
    plt.axvline(
        q75,
        color="#f39c12",
        linestyle=":",
        linewidth=1.5,
        label=f"75% Percentil ({q75:.0f} uds)",
    )

    plt.title(
        "Distribución de Stock\nAnálisis Cuantitativo",
        fontsize=14,
        pad=20,
        color="#2c3e50",
        fontweight="bold",
    )
    plt.xlabel("Unidades en Stock", fontsize=12, labelpad=10, color="#2c3e50")
    plt.ylabel("Número de Productos", fontsize=12, labelpad=10, color="#2c3e50")

    legend = plt.legend(frameon=True, facecolor="white")
    for text in legend.get_texts():
        text.set_color("#2c3e50")

    REPORTS_PATH.mkdir(parents=True, exist_ok=True)
    filepath = REPORTS_PATH / "stock_analizado_confiable.png"
    plt.savefig(filepath, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"✅ Gráfico generado en:\n{filepath.absolute()}")


def grafico_valor_categoria(df: pd.DataFrame) -> None:
    """
    Barras horizontales con valor total por categoría, filtrando valores inválidos.
    """
    plt.figure(figsize=(12, 7), dpi=120)

    df = df.copy()
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce").fillna(0)
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0)
    df["valor_total"] = df["cantidad"] * df["precio"]

    categorias_validas = {
        "Ferretería",
        "Electricidad",
        "Herramientas",
        "Jardinería",
        "Pintura",
        "Electrónica",
        "Construcción",
        "Fontanería",
    }

    df["categoria"] = (
        df["categoria"]
        .astype(str)
        .str.strip()
        .apply(lambda x: x if x in categorias_validas else "Otros")
    )

    datos = (
        df.groupby("categoria")["valor_total"]
        .sum()
        .sort_values()
        .loc[lambda x: x > 0]
    )

    ax = datos.plot(
        kind="barh",
        color="#2ca02c",
        edgecolor="white",
        alpha=0.8,
        width=0.85,
    )

    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(
            lambda x, _: f"${x / 1000:,.1f}K"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    )

    plt.title("Valor Real por Categoría (miles USD)", pad=20, fontweight="bold")
    plt.xlabel("Valor Total (USD)", labelpad=10)
    plt.grid(axis="x", linestyle=":", alpha=0.3)
    plt.tight_layout()

    filepath = REPORTS_PATH / "valor_categoria_real.png"
    plt.savefig(filepath, bbox_inches="tight", dpi=300, facecolor="white")
    plt.close()

    print(f"✅ Gráfico de categorías guardado en: {filepath.absolute()}")
