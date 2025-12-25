import pandas as pd


def data_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza con:
    - Validación estricta de códigos
    - Formateo consistente de decimales
    - Filtrado robusto de filas inválidas
    """
    df_clean = df.copy()

    # 1. Limpieza básica (strings)
    for col in ["codigo", "nombre", "categoria", "ubicacion"]:
        df_clean[col] = df_clean[col].astype(str).str.strip()

    # 2. Normalización crítica de códigos (PR + 3-4 dígitos)
    df_clean["codigo"] = (
        df_clean["codigo"]
        .str.upper()
        .str.extract(r"(PR?\s?(\d{3,4}))")[0]  # Captura PR + 3-4 dígitos
        .str.replace(r"\D", "", regex=True)  # Elimina caracteres no numéricos
        .apply(lambda x: f"PR{x.zfill(3)}" if pd.notna(x) and x.isdigit() else pd.NA)
    )

    # 3. Filtrado de filas sin código válido
    df_clean = df_clean.dropna(subset=["codigo"])

    # 4. Limpieza numérica con control estricto
    df_clean["cantidad"] = (
        pd.to_numeric(df_clean["cantidad"], errors="coerce").abs().fillna(0).astype(int)
    )
    df_clean["precio"] = (
        pd.to_numeric(df_clean["precio"], errors="coerce").abs().round(2)
    )

    # 5. Cálculo preciso de valor_total
    df_clean["valor_total"] = (df_clean["cantidad"] * df_clean["precio"]).round(2)

    # 6. Filtrado final (asegura todas las columnas clave)
    df_clean = (
        df_clean[
            (df_clean["cantidad"] >= 0)  # permitir agotados
            & (df_clean["precio"] > 0)
            & (df_clean["nombre"].str.len() > 3)
        ]
        .drop_duplicates(subset=["codigo", "nombre"])
    )

    # 7. Ordenamiento por código
    df_clean = df_clean.sort_values("codigo").reset_index(drop=True)

    # Reporte
    print("\n=== REPORTE FINAL ===")
    print(f"Registros válidos: {len(df_clean)}")
    print(f"Valor total: ${df_clean['valor_total'].sum():,.2f}")
    print("\n5 primeros registros:")
    print(df_clean.head().to_string(index=False))

    return df_clean
