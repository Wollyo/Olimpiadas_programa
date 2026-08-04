import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path para importar `src`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.merger import read_data, validate_records
p = "Data/Inscripción/INFORMACION GENERAL ESTUDIANTES INSCRITOS ORM 2026 - Hoja 1.csv"
rows = read_data(p)
_, warnings = validate_records(rows)
print("TOTAL_WARNINGS:", len(warnings))
print("TOTAL_ROWS:", len(rows))
print("FIRST_30_WARNINGS:")
for w in warnings[:30]:
    print(w)
