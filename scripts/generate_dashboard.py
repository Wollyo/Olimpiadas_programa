import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.merger import read_data, analyze_missing_and_suggestions, Dashboard, normalize_levels

p = "Data/Inscripción/INFORMACION GENERAL ESTUDIANTES INSCRITOS ORM 2026 - Hoja 1.csv"
rows = read_data(p)

print('Ejecutando análisis de faltantes y sugerencias...')
report = analyze_missing_and_suggestions(rows)
print('\nFaltantes por campo:')
for k, v in report['missing_counts'].items():
    print(f" - {k}: {v}")

print('\nIDs con caracteres no numéricos (ejemplos):')
for t in report['id_non_numeric'][:10]:
    print(' -', t)

print('\nSugerencias de limpieza de ID:')
for t in report['id_suggestions'][:10]:
    print(' - fila', t[0], ':', t[1], '-> sugerido:', t[2])

if report['similar_schools']:
    print('\nPosibles nombres de colegio similares (agrupar):')
    count = 0
    for k, v in list(report['similar_schools'].items())[:10]:
        print(' -', k, '->', v)
        count += 1
        if count >= 10:
            break

# dashboard
print('\nConstruyendo dashboard...')
# normalizar niveles antes del dashboard
rows = normalize_levels(rows)
db = Dashboard(rows)
db.print_summary()
