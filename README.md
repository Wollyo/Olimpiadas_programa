# Dashboard de inscripciones - Olimpiadas Regionales

Este proyecto permite cargar un archivo de inscripciones, limpiar y organizar los datos, y visualizar la información en un dashboard interactivo con filtros, métricas y exportaciones.

## Qué hace la app

La aplicación:
- Carga archivos CSV o Excel desde la interfaz.
- Detecta datos incompletos o inconsistentes.
- Normaliza nombres, departamentos, municipios, colegios y niveles.
- Convierte los nombres y apellidos a mayúsculas.
- Permite filtrar por departamento, municipio, colegio, tipo de colegio, nivel y género.
- Descarga los resultados filtrados en CSV o Excel.

## Requisitos

- Python 3.10 o superior
- Entorno virtual recomendado
- Dependencias incluidas en el archivo requirements.txt

## Instalación en Windows PowerShell

```powershell
cd C:\Users\madar\Olimpiadas_programa
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecutar la app

```powershell
streamlit run scripts/streamlit_dashboard.py
```

## Cómo usarla

1. Abrir la aplicación en el navegador.
2. Subir un archivo CSV o Excel desde la parte superior.
3. Esperar a que se carguen los datos.
4. Usar los filtros laterales para explorar la información.
5. Descargar los resultados filtrados en CSV o Excel.

## Qué archivo subir idealmente

Lo ideal es subir un archivo con columnas claras y consistentes, por ejemplo:
- Nombre o Nombres
- Apellido o Apellidos
- Identificación
- Departamento
- Municipio
- Colegio o Institución
- Nivel
- Sector
- Género

El archivo que mejor encaja con este proyecto es el que está en:
- Data/Inscripción/INFORMACION GENERAL ESTUDIANTES INSCRITOS ORM 2026 - Hoja 1.csv

### Recomendaciones para el archivo
- Preferir archivos CSV o Excel bien formados.
- Mantener nombres de columnas simples y consistentes.
- Evitar celdas vacías en campos clave como nombre, apellido o identificación.
- Si hay diferentes formas de escribir el nivel, la app intenta normalizarlas a: Junior, Básico, Medio y Avanzado.

## Archivos importantes

- scripts/streamlit_dashboard.py: lógica de la app, filtros y exportaciones.
- Data/Inscripción/: carpeta con los archivos de inscripción.
- requirements.txt: dependencias del proyecto.

## Notas

- La app inicia en un estado limpio y espera a que subas un archivo antes de mostrar contenido.
- Los nombres y apellidos se muestran en mayúsculas.
- Si Streamlit pregunta por telemetría, puedes desactivar la recopilación creando un archivo de configuración en %USERPROFILE%/.streamlit/config.toml con:

```toml
[browser]
gatherUsageStats = false
```