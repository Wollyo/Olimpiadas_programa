import sys, os, csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.merger import read_data, normalize_levels, normalize_ids, clean_for_dashboard

INPUT = "Data/Inscripción/INFORMACION GENERAL ESTUDIANTES INSCRITOS ORM 2026 - Hoja 1.csv"
OUT_DIR = "Data/processed"
OUT_PATH = os.path.join(OUT_DIR, "cleaned_dashboard.csv")

os.makedirs(OUT_DIR, exist_ok=True)

rows = read_data(INPUT)
# normalizaciones
rows = normalize_levels(rows)
rows = normalize_ids(rows)
cleaned = clean_for_dashboard(rows)

# escribir CSV con encabezados fijos
headers = [
    'Numero identificacion', 'Nombres', 'Apellidos', 'Genero', 'Grado', 'Calendario',
    'Talla posible de camiseta', 'Nombre del colegio o institución educativa',
    'Departamento', 'Municipio', '_id_cleaned', '_level_normalized'
]

with open(OUT_PATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for r in cleaned:
        writer.writerow({h: r.get(h, '') for h in headers})

print('Cleaned CSV escrito en:', OUT_PATH)
print('Filas escritas:', len(cleaned))
