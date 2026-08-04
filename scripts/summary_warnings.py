import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.merger import read_data, validate_records
p = "Data/Inscripción/INFORMACION GENERAL ESTUDIANTES INSCRITOS ORM 2026 - Hoja 1.csv"
rows = read_data(p)
_, warnings = validate_records(rows)

cats = {
    'nombres_vacios': [w for w in warnings if "campo de nombres vacío" in w.lower()],
    'apellidos_vacios': [w for w in warnings if "campo de apellidos vacío" in w.lower()],
    'id_vacios': [w for w in warnings if "campo de identidad vacío" in w.lower()],
    'id_no_numericos': [w for w in warnings if "id contiene caracteres no numéricos" in w.lower()],
}
print('TOTAL_ROWS:', len(rows))
print('TOTAL_WARNINGS:', len(warnings))
for k,v in cats.items():
    print(f"{k}: {len(v)}")
    for item in v[:5]:
        print('  -', item)
    print()
