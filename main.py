from scripts import data_analysis, data_clean, data_load
import os

# Configuración de rutas
DATA_PATH = "/home/pauloenrique/Documents/Development/makeAutomatic/inventory_management/data"
BASE_NAME = "inventario"  # Nombre base sin extensión


def main():
    print("Welcome Paulo Enrique!")
    print("Cargando inventario...")

    try:
        # Busca primero .ods, luego .csv y .xlsx
        file_formats = [".ods", ".csv", ".xlsx"]
        file_path = None

        for ext in file_formats:
            potential_path = f"{DATA_PATH}/{BASE_NAME}{ext}"
            if os.path.exists(potential_path):
                file_path = potential_path
                break  # Sale del bucle al encontrar un archivo válido

        if file_path is None:
            raise FileNotFoundError("No se encontró un archivo de inventario válido en formato .ods, .csv o .xlsx.")

        # Carga de datos
        df = data_load.load_data(file_path)
        print("\n✅ Inventario cargado exitosamente desde:", file_path)
        print("Muestra de datos originales:")
        print(df.head(3))

        # Limpieza de datos
        df = data_clean.data_clean(df)
        print("\n🧹 Datos limpiados correctamente")

        # Análisis
        print("\n📊 === EJECUTANDO ANÁLISIS AVANZADO ===")
        data_analysis.analizar_inventario(df)

        # Guardado automático con la misma extensión del archivo cargado
        file_ext = os.path.splitext(file_path)[1]
        clean_path = f"{DATA_PATH}/{BASE_NAME}_clean{file_ext}"

        if file_ext == ".csv":
            df.to_csv(clean_path, index=False)
        else:
            df.to_excel(clean_path, index=False)

        print(f"\n💾 Versión limpia guardada en: {clean_path}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except ValueError as e:
        print(f"\n❌ Error en los datos: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


if __name__ == "__main__":
    main()
