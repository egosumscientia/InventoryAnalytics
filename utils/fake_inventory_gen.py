import random
import csv
import openpyxl
import pandas as pd
from faker import Faker

# Configuración inicial
fake = Faker()
random.seed(42)  # Para resultados reproducibles

# Categorías y ubicaciones posibles
CATEGORIAS = [
    "Ferretería", "Electrónica", "Fontanería", "Jardinería",
    "Construcción", "Herramientas", "Electricidad", "Pintura"
]
UBICACIONES = [f"Estante {letra}{num}" for letra in "ABCDEF" for num in range(1, 10)]


# Funciones para generar datos con posibles errores
def generar_codigo(index):
    if random.random() < 0.1:  # 10% de probabilidad de error
        errors = ["", "PR", f"PR{index:02}", f"PR{index:03}XX", f"PR{index}"]
        return random.choice(errors)
    return f"PR{index:03}"


def generar_nombre(categoria):
    nombres = {
        "Ferretería": ["Tornillo", "Tuerca", "Arandela", "Clavo", "Perno"],
        "Electrónica": ["Cable", "Resistor", "Condensador", "LED", "Interruptor"],
        "Fontanería": ["Tubo", "Válvula", "Grifo", "Sifón", "Junta"],
        "Jardinería": ["Manguera", "Regadera", "Pala", "Rastrillo", "Tijeras"],
        "Construcción": ["Ladrillo", "Cemento", "Arena", "Viga", "Teja"],
        "Herramientas": ["Martillo", "Destornillador", "Alicate", "Llave", "Sierra"],
        "Electricidad": ["Fusible", "Caja", "Portalámparas", "Cinta", "Conector"],
        "Pintura": ["Rodillo", "Brocha", "Bandeja", "Lija", "Espátula"]
    }

    base = random.choice(nombres.get(categoria, ["Producto"]))

    if random.random() < 0.1:  # 10% de probabilidad de error
        return base  # Nombre incompleto
    elif random.random() < 0.05:  # 5% de probabilidad de otro error
        return fake.word()  # Nombre sin sentido

    modificadores = {
        "Ferretería": ["M6", "M8", "Hexagonal", "Allen", "Inoxidable"],
        "Electrónica": ["UTP", "Coaxial", "5m", "10A", "220V"],
        "Fontanería": ["1/2\"", "3/4\"", "PVC", "Cobre", "Flexible"],
        "Jardinería": ["Plástico", "Metal", "Grande", "Pequeño", "Profesional"],
        "Construcción": ["Hueco", "Macizo", "25kg", "Reforzado", "Termoaislante"],
        "Herramientas": ["Acero", "Profesional", "15cm", "300g", "Ergonómico"],
        "Electricidad": ["Aislante", "10m", "Rojo", "Azul", "Amarillo"],
        "Pintura": ["5cm", "Cerda", "Espuma", "Plástico", "Metal"]
    }

    return f"{base} {random.choice(modificadores.get(categoria, ['Standard']))}"


def generar_cantidad():
    if random.random() < 0.1:  # 10% de probabilidad de error
        return random.choice([-1, "N/A", "muchos", "", 1000])
    return random.randint(1, 1000)


def generar_precio():
    if random.random() < 0.1:  # 10% de probabilidad de error
        # Valores de error más realistas
        return random.choice([-0.5, "gratis", "", round(random.uniform(1000.01, 1500.0), 2)])
    return round(random.uniform(1.0, 1000.0), 2)


def generar_categoria():
    if random.random() < 0.1:  # 10% de probabilidad de error
        return random.choice(["", "Varios", "Otro", fake.word()])
    return random.choice(CATEGORIAS)


def generar_ubicacion():
    if random.random() < 0.1:  # 10% de probabilidad de error
        return random.choice(["", "Almacén", "Desconocido", "Perdido", fake.word()])
    return random.choice(UBICACIONES)


# Generar el inventario
def generar_inventario(num_items=1000):
    inventario = []
    for i in range(1, num_items + 1):
        categoria = generar_categoria()
        item = [
            generar_codigo(i),
            generar_nombre(categoria),
            generar_cantidad(),
            generar_precio(),
            categoria,
            generar_ubicacion()
        ]
        inventario.append(item)
    return inventario


# Guardar en diferentes formatos
def guardar_inventario(inventario, nombre_base="inventario"):
    # Encabezados
    headers = ["codigo", "nombre", "cantidad", "precio", "categoria", "ubicacion"]

    # CSV
    with open(f"{nombre_base}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(inventario)

    # Excel (XLSX)
    df = pd.DataFrame(inventario, columns=headers)
    df.to_excel(f"{nombre_base}.xlsx", index=False)

    # ODS
    df.to_excel(f"{nombre_base}.ods", engine="odf", index=False)


# Ejecución principal
if __name__ == "__main__":
    print("Generando inventario...")
    inventario = generar_inventario(1000)
    guardar_inventario(inventario)
    print("Inventario generado en formatos CSV, XLSX y ODS con aproximadamente 10% de errores.")