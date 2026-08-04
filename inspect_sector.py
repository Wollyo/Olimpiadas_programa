import pandas as pd
p = r'C:\Users\madar\Olimpiadas_programa\Data\Inscripción\INFORMACION GENERAL ESTUDIANTES INSCRITOS ORM 2026 - Hoja 1.csv'
df = pd.read_csv(p, dtype=str, nrows=20)
print(df.columns.tolist())
for col in ['Sector', 'sector', 'Tipo', 'Tipo de colegio', 'tipo', 'SECTOR']:
    if col in df.columns:
        print(f'\nCOL {col}')
        print(df[col].head(20).tolist())
