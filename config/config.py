from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

INSCRIPCIONES_DIR = DATA_DIR / "inscripciones"

PRUEBAS_DIR = DATA_DIR / "pruebas"

RESULTADOS_DIR = DATA_DIR / "resultados"

FUZZY_SCORE = 95

LOG_LEVEL = "INFO"