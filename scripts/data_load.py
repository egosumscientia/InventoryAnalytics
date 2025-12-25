import pandas as pd
import os
from typing import Union, List

SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.ods']


def load_data(file_path: str, try_alternatives: bool = True) -> Union[pd.DataFrame, None]:
    """
    Carga datos de un archivo (CSV, XLSX, ODS) con manejo robusto de errores.

    Args:
        file_path: Ruta completa al archivo
        try_alternatives: Si True, intenta con otras extensiones si el archivo no existe

    Returns:
        DataFrame con los datos cargados

    Raises:
        FileNotFoundError: Si no se encuentra ningún archivo compatible
        ValueError: Si la extensión no es soportada
        Exception: Para otros errores de carga
    """
    try:
        original_path = file_path
        file_ext = os.path.splitext(file_path)[1].lower()

        # Verificar extensión soportada
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Extensión '{file_ext}' no soportada. Use: {SUPPORTED_EXTENSIONS}")

        # Si el archivo no existe y se permiten alternativas
        if not os.path.exists(file_path) and try_alternatives:
            base_path = os.path.splitext(file_path)[0]
            for ext in SUPPORTED_EXTENSIONS:
                if ext == file_ext:  # Saltar la extensión original ya que no existe
                    continue
                alternative_path = base_path + ext
                if os.path.exists(alternative_path):
                    file_path = alternative_path
                    print(f"⚠ Archivo {original_path} no encontrado. Cargando {alternative_path}")
                    break
            else:
                available_files = [f for f in os.listdir(os.path.dirname(file_path))
                                   if any(f.endswith(ext) for ext in SUPPORTED_EXTENSIONS)]
                raise FileNotFoundError(
                    f"No se encontró {original_path} ni alternativas. Archivos disponibles: {available_files}"
                )

        # Cargar según extensión
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext == '.xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_ext == '.ods':
            df = pd.read_excel(file_path, engine='odf')
        else:
            raise ValueError(f"Extensión no manejada: {file_ext}")

        if df.empty:
            print("⚠ Advertencia: El archivo está vacío")

        return df

    except pd.errors.EmptyDataError:
        raise ValueError(f"El archivo {file_path} está vacío o corrupto")
    except pd.errors.ParserError:
        raise ValueError(f"Error al parsear el archivo {file_path}")
    except Exception as e:
        raise Exception(f"Error al cargar {file_path}: {str(e)}")


def find_actual_file_path(base_path: str) -> str:
    """
    Encuentra la ruta real del archivo con cualquier extensión soportada.

    Args:
        base_path: Ruta base sin extensión (ej. '/ruta/archivo')

    Returns:
        Ruta completa del archivo encontrado

    Raises:
        FileNotFoundError: Si no se encuentra ningún archivo compatible
    """
    for ext in SUPPORTED_EXTENSIONS:
        file_path = base_path + ext
        if os.path.exists(file_path):
            return file_path
    raise FileNotFoundError(
        f"No se encontró archivo con extensiones {SUPPORTED_EXTENSIONS} en {base_path}"
    )