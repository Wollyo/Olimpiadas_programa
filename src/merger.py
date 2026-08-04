"""Herramientas para cargar, validar y procesar calificaciones.

Uso básico desde línea de comandos:
python -m src.merger path/al/archivo.csv

El módulo lee CSV (separador coma), detecta celdas vacías y valida números
de identidad (solo dígitos y longitud típica entre 6 y 12). Genera warnings
en consola y muestra un resumen y una tabla de calificaciones procesadas.
"""
from typing import List, Dict, Tuple, Any
import csv
import sys
import re
from collections import Counter, defaultdict
from difflib import get_close_matches
import unicodedata
import json
from pathlib import Path


ID_PATTERN = re.compile(r"^\d{6,12}$")


def read_data(path: str, encoding: str = "utf-8") -> List[Dict[str, str]]:
    """Leer un archivo de datos. Soporta CSV y Excel (.xlsx).

    Para Excel intenta usar `pandas`. Si no está instalado, lanza un mensaje
    indicando cómo instalar las dependencias.
    """
    path_lower = path.lower()
    if path_lower.endswith(".xlsx") or path_lower.endswith(".xls"):
        try:
            import pandas as pd
        except Exception:
            raise ImportError(
                "Para leer archivos Excel necesita instalar 'pandas' y 'openpyxl'.\n"
                "Ejemplo: pip install pandas openpyxl"
            )
        df = pd.read_excel(path, engine="openpyxl")
        # convertir a lista de dicts con strings
        rows: List[Dict[str, str]] = []
        for _, row in df.fillna("").iterrows():
            rows.append({str(k): ("" if v is None else str(v).strip()) for k, v in row.items()})
        return rows

    # por defecto manejar como CSV
    rows: List[Dict[str, str]] = []
    with open(path, encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v.strip() if v is not None else "") for k, v in r.items()})
    return rows


def validate_records(rows: List[Dict[str, str]], id_field_candidates: List[str] = None) -> Tuple[List[Dict[str, str]], List[str]]:
    """Valida celdas vacías y números de identidad, y comprueba nombres/apellidos.

    Devuelve (rows, warnings)
    """
    warnings: List[str] = []
    if id_field_candidates is None:
        id_field_candidates = ["numero identificacion", "numero de identificacion", "identificacion", "id", "identidad", "documento", "dni", "cedula"]

    name_field_candidates = ["nombres", "nombre", "nombre estudiante", "nombre completo"]
    surname_field_candidates = ["apellidos", "apellido", "apellido estudiante"]

    # Detectar campo de id
    if not rows:
        warnings.append("El archivo no contiene filas.")
        return rows, warnings

    headers = list(rows[0].keys())
    id_field = None
    for cand in id_field_candidates:
        for h in headers:
            if h.lower().strip() == cand:
                id_field = h
                break
        if id_field:
            break

    if not id_field:
        # buscar coincidencias parciales
        for h in headers:
            if any(tok in h.lower() for tok in ("numero", "identificacion", "identificaci")):
                id_field = h
                break

    if not id_field and headers:
        id_field = headers[0]
        warnings.append(f"No se detectó explícitamente campo de identidad; se usará '{id_field}'.")

    # detectar nombres y apellidos
    name_field = None
    surname_field = None
    for cand in name_field_candidates:
        for h in headers:
            if h.lower().strip() == cand:
                name_field = h
                break
        if name_field:
            break

    for cand in surname_field_candidates:
        for h in headers:
            if h.lower().strip() == cand:
                surname_field = h
                break
        if surname_field:
            break

    # heurística: si no encuentra apellidos/nombres exactos, buscar por token
    if not name_field:
        for h in headers:
            if "nombre" in h.lower() and "docente" not in h.lower():
                name_field = h
                break
    if not surname_field:
        for h in headers:
            if "apell" in h.lower() and "docente" not in h.lower():
                surname_field = h
                break

    # Validaciones por fila
    for i, row in enumerate(rows, start=2):
        # revisar celdas vacías en la fila (lista de columnas vacías)
        empty_cols = [k for k, v in row.items() if v is None or v == ""]
        if empty_cols:
            warnings.append(f"Fila {i}: celdas vacías en columnas: {', '.join(empty_cols)}")

        # validar nombres/apellidos (si existen campos detectados)
        if name_field:
            name_val = (row.get(name_field) or "").strip()
            if name_val == "":
                warnings.append(f"Fila {i}: campo de nombres vacío ('{name_field}')")
        if surname_field:
            surname_val = (row.get(surname_field) or "").strip()
            if surname_val == "":
                warnings.append(f"Fila {i}: campo de apellidos vacío ('{surname_field}')")

        # validar id: no vacío, solo dígitos, longitud razonable
        if id_field:
            val = (row.get(id_field) or "").strip()
            if val == "":
                warnings.append(f"Fila {i}: campo de identidad vacío ('{id_field}')")
            else:
                if not val.isdigit():
                    warnings.append(f"Fila {i}: ID contiene caracteres no numéricos en '{id_field}': '{val}'")
                if not (6 <= len(val) <= 12):
                    warnings.append(f"Fila {i}: longitud inusual para ID ({len(val)}) en '{id_field}': '{val}'")

    return rows, warnings


def summary(rows: List[Dict[str, str]], school_field_candidates: List[str] = None) -> Dict[str, Any]:
    """Genera resumen: total registros, colegios únicos y desglose básico por colegio."""
    if school_field_candidates is None:
        school_field_candidates = ["colegio", "escuela", "institucion", "instituto", "school"]

    if not rows:
        return {"total": 0, "unique_schools": 0, "by_school": {}}

    headers = list(rows[0].keys())
    school_field = None
    for cand in school_field_candidates:
        for h in headers:
            if h.lower().strip() == cand:
                school_field = h
                break
        if school_field:
            break

    if not school_field:
        # buscar heurística
        for h in headers:
            if "coleg" in h.lower() or "escuel" in h.lower() or "instit" in h.lower():
                school_field = h
                break

    counts = Counter()
    for r in rows:
        key = (r.get(school_field) or "(sin colegio)").strip()
        counts[key] += 1

    return {"total": len(rows), "unique_schools": len([k for k in counts if k and k != "(sin colegio)"]), "by_school": dict(counts)}


def process_grades(rows: List[Dict[str, str]], grade_fields: List[str] = None) -> List[Dict[str, Any]]:
    """Procesa calificaciones: normaliza a float, calcula promedio si hay múltiples campos de nota.

    Devuelve lista de registros con campos adicionales: `_grades_processed` y `_average`.
    """
    processed: List[Dict[str, Any]] = []
    if not rows:
        return processed

    headers = list(rows[0].keys())
    # Si no se indican campos de nota, detectar por heurística
    if grade_fields is None:
        grade_fields = [h for h in headers if any(tok in h.lower() for tok in ("nota", "calif", "score", "puntos"))]

    for r in rows:
        rec = dict(r)
        grades = []
        for g in grade_fields:
            val = r.get(g, "")
            try:
                # reemplazar coma decimal
                if isinstance(val, str):
                    v = val.replace(",", ".")
                else:
                    v = val
                f = float(v) if v != "" else None
            except Exception:
                f = None
            if f is not None:
                grades.append(f)

        rec["_grades_processed"] = grades
        if grades:
            rec["_average"] = round(sum(grades) / len(grades), 2)
        else:
            rec["_average"] = None
        processed.append(rec)

    return processed


def analyze_missing_and_suggestions(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    """Analiza campos faltantes y genera sugerencias de corrección simples.

    Retorna un dict con conteos, ejemplos y sugerencias detectadas.
    """
    required = [
        "Numero identificacion",
        "Nombres",
        "Apellidos",
        "Nombre del colegio o institución educativa",
        "Departamento",
        "Municipio",
    ]

    missing_counts = Counter()
    missing_examples = defaultdict(list)
    id_non_numeric = []
    id_suggestions = []
    name_case_suggestions = []
    email_problems = []

    # collect school names for fuzzy grouping
    school_names = []

    for i, r in enumerate(rows, start=2):
        for f in required:
            val = (r.get(f) or "").strip()
            if val == "":
                missing_counts[f] += 1
                if len(missing_examples[f]) < 5:
                    missing_examples[f].append((i, r))

        # ID checks
        idv = (r.get("Numero identificacion") or "").strip()
        if idv and not idv.isdigit():
            id_non_numeric.append((i, idv))
            cleaned = re.sub(r"\D", "", idv)
            if 6 <= len(cleaned) <= 12:
                id_suggestions.append((i, idv, cleaned))

        # name case suggestion
        n = (r.get("Nombres") or "").strip()
        if n and n.islower():
            name_case_suggestions.append((i, n, n.title()))

        # email quick checks
        em = (r.get("Email de contacto") or "").strip()
        if em and ("@" not in em or " " in em):
            email_problems.append((i, em))

        school = (r.get("Nombre del colegio o institución educativa") or "").strip()
        if school:
            school_names.append(school)

    # fuzzy grouping for school names
    unique_schools = list({s for s in school_names})
    similar = {}
    for s in unique_schools:
        matches = get_close_matches(s, unique_schools, n=5, cutoff=0.85)
        if len(matches) > 1:
            similar[s] = matches

    return {
        "missing_counts": dict(missing_counts),
        "missing_examples": {k: [(idx, ) for (idx, _) in v] for k, v in missing_examples.items()},
        "id_non_numeric": id_non_numeric,
        "id_suggestions": id_suggestions,
        "name_case_suggestions": name_case_suggestions,
        "email_problems": email_problems,
        "similar_schools": similar,
    }


def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


LEVEL_CANONICAL = {
    'junior': 'Junior',
    'junio': 'Junior',
    'júnior': 'Junior',
    'júnior': 'Junior',
    'basico': 'Básico',
    'básico': 'Básico',
    'basico ': 'Básico',
    'básicO': 'Básico',
    'medio': 'Medio',
    'avanzado': 'Avanzado',
}


def normalize_levels(rows: List[Dict[str, str]], field_name: str = None) -> List[Dict[str, str]]:
    """Normaliza el campo de nivel a cuatro valores canónicos: Junior, Básico, Medio, Avanzado.

    Añade/actualiza la clave `_level_normalized` en cada registro.
    Si `field_name` no se proporciona, intenta inferirlo.
    """
    if not rows:
        return rows

    headers = list(rows[0].keys())
    if not field_name:
        for h in headers:
            if 'nivel' in h.lower():
                field_name = h
                break
    if not field_name:
        return rows

    for r in rows:
        raw = (r.get(field_name) or '').strip()
        key = _strip_accents(raw.lower())
        key = key.replace('.', '').replace('  ', ' ').strip()
        # try direct map
        norm = None
        if key in LEVEL_CANONICAL:
            norm = LEVEL_CANONICAL[key]
        else:
            # try matching tokens
            for k, v in LEVEL_CANONICAL.items():
                if k in key:
                    norm = v
                    break
        if not norm and raw:
            # fallback: title-case the value
            norm = raw.title()
        r['_level_normalized'] = norm if norm else ''
        # reemplazar el campo original para simplificar resúmenes posteriores
        if norm:
            r[field_name] = norm

    return rows


def normalize_ids(rows: List[Dict[str, str]], id_field: str = None) -> List[Dict[str, str]]:
    """Limpia caracteres no numéricos en el campo de ID y guarda el original en `_raw_id`.
    No sobrescribe si la limpieza deja longitud inválida.
    """
    if not rows:
        return rows
    headers = list(rows[0].keys())
    if not id_field:
        for h in headers:
            if 'ident' in h.lower() or 'numero' in h.lower():
                id_field = h
                break
    if not id_field:
        return rows

    for r in rows:
        orig = (r.get(id_field) or '').strip()
        r['_raw_id'] = orig
        if not orig:
            r['_id_cleaned'] = ''
            continue
        cleaned = re.sub(r'\D', '', orig)
        if 6 <= len(cleaned) <= 12:
            r[id_field] = cleaned
            r['_id_cleaned'] = cleaned
        else:
            r['_id_cleaned'] = cleaned

    return rows


def normalize_text(value: str, *, to_title: bool = True) -> str:
    """Normaliza texto: quita acentos, dobles espacios, y aplica title-case o upper.

    Devuelve cadena vacía si el valor es falsy.
    """
    if not value:
        return ""
    s = str(value).strip()
    s = _strip_accents(s)
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    if to_title:
        # Title-case pero manteniendo algunas preposiciones en minúscula no necesario ahora
        return s.title()
    return s


def normalize_school_name(value: str) -> str:
    """Normaliza nombre de colegio para unificarlos (quita extras y title-case)."""
    return normalize_text(value, to_title=True)


def normalize_department(value: str) -> str:
    v = normalize_text(value, to_title=True)
    # aplicar mapa si existe
    mapped = _apply_norm_map('departments', v)
    return mapped


def normalize_municipality(value: str) -> str:
    v = normalize_text(value, to_title=True)
    mapped = _apply_norm_map('municipalities', v)
    return mapped


_NORM_MAPS = None


def load_norm_maps(path: str = None) -> Dict[str, Dict[str, str]]:
    """Carga mapas de normalización desde `config/normalization.json` si existe.

    Estructura esperada JSON:
    {
      "departments": {"Valle del cauca": "Valle Del Cauca", ...},
      "municipalities": {"cali": "Cali", ...},
      "schools": {"ie gabo": "IE Gabo", ...}
    }
    """
    global _NORM_MAPS
    if _NORM_MAPS is not None:
        return _NORM_MAPS
    if path is None:
        p = Path(__file__).resolve().parents[1] / 'config' / 'normalization.json'
    else:
        p = Path(path)
    if not p.exists():
        _NORM_MAPS = {}
        return _NORM_MAPS
    try:
        with open(p, encoding='utf-8') as f:
            data = json.load(f)
            # normalize keys and values
            normed = {}
            for k, m in data.items():
                normed[k] = {normalize_text(k2).lower(): normalize_text(v2) for k2, v2 in m.items()}
            _NORM_MAPS = normed
            return _NORM_MAPS
    except Exception:
        _NORM_MAPS = {}
        return _NORM_MAPS


def _apply_norm_map(kind: str, value: str) -> str:
    """Aplica mapa de normalización cargado si existe; caso contrario devuelve `value`."""
    maps = load_norm_maps()
    if not maps:
        return value
    bucket = maps.get(kind, {})
    if not value:
        return value
    key = normalize_text(value).lower()
    return bucket.get(key, value)


def clean_for_dashboard(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Genera una versión limpia de los registros solo con columnas necesarias y normalizadas.

    Columnas devueltas: `Numero identificacion`, `Nombres`, `Apellidos`, `Genero`, `Grado`,
    `Calendario`, `Talla posible de camiseta`, `Nombre del colegio o institución educativa`,
    `Departamento`, `Municipio` y campos auxiliares `_id_cleaned`, `_level_normalized`.
    """
    out: List[Dict[str, str]] = []
    for r in rows:
        nr = {}
        nr['Numero identificacion'] = r.get('Numero identificacion') or r.get('Numero identificación') or ''
        nr['Nombres'] = normalize_text(r.get('Nombres') or r.get('Nombre') or '')
        nr['Apellidos'] = normalize_text(r.get('Apellidos') or r.get('Apellido') or '')
        nr['Genero'] = normalize_text(r.get('Genero') or r.get('Genero') or '', to_title=True)
        nr['Grado'] = normalize_text(r.get('Grado') or '')
        nr['Calendario'] = normalize_text(r.get('Calendario') or '')
        nr['Talla posible de camiseta'] = normalize_text(r.get('Talla posible de camiseta') or r.get('Talla posible de camiseta', ''))
        school_field = 'Nombre del colegio o institución educativa'
        nr['Nombre del colegio o institución educativa'] = normalize_school_name(r.get(school_field) or '')
        nr['Departamento'] = normalize_department(r.get('Departamento') or '')
        nr['Municipio'] = normalize_municipality(r.get('Municipio') or '')
        # mantener campos auxiliares si existen
        nr['_level_normalized'] = r.get('_level_normalized', '')
        nr['_id_cleaned'] = r.get('_id_cleaned', '')
        out.append(nr)
    return out


class Dashboard:
    """Clase simple para construir y mostrar un resumen tipo dashboard del dataset."""

    def __init__(self, rows: List[Dict[str, str]]):
        self.rows = rows

    def summary(self) -> Dict[str, Any]:
        total = len(self.rows)
        schools = Counter()
        departments = Counter()
        municipalities = Counter()
        levels = Counter()

        for r in self.rows:
            schools[(r.get("Nombre del colegio o institución educativa") or "(sin colegio)").strip()] += 1
            departments[(r.get("Departamento") or "(sin departamento)").strip()] += 1
            municipalities[(r.get("Municipio") or "(sin municipio)").strip()] += 1
            levels[(r.get("Nivel (junio,basico, medio o avanzado)") or "(sin nivel)").strip()] += 1

        return {
            "total_students": total,
            "unique_schools": len([s for s in schools if s and s != "(sin colegio)"]),
            "top_schools": schools.most_common(10),
            "by_department": departments.most_common(),
            "by_municipality": municipalities.most_common(10),
            "by_level": dict(levels),
        }

    def print_summary(self) -> None:
        s = self.summary()
        print("\n--- DASHBOARD RESUMEN ---")
        print(f"Total estudiantes: {s['total_students']}")
        print(f"Colegios únicos: {s['unique_schools']}")
        print("Top colegios:")
        for name, cnt in s["top_schools"]:
            print(f" - {name}: {cnt}")
        print("\nPor departamento (top):")
        for name, cnt in s["by_department"][:10]:
            print(f" - {name}: {cnt}")
        print("\nPor municipio (top):")
        for name, cnt in s["by_municipality"]:
            print(f" - {name}: {cnt}")
        print("\nDistribución por nivel:")
        for lvl, cnt in s["by_level"].items():
            print(f" - {lvl}: {cnt}")


def print_warnings(warnings: List[str]) -> None:
    if not warnings:
        print("No se detectaron problemas de validación.")
        return
    print("ADVERTENCIAS:")
    for w in warnings:
        print(f" - {w}")


def print_summary(summary_info: Dict[str, Any], top: int = 10) -> None:
    print("\nRESUMEN RÁPIDO:")
    print(f"Total registros: {summary_info.get('total', 0)}")
    print(f"Colegios únicos: {summary_info.get('unique_schools', 0)}")
    print("Desglose por colegio (top):")
    by_school = summary_info.get("by_school", {})
    sorted_schools = sorted(by_school.items(), key=lambda x: -x[1])[:top]
    for name, cnt in sorted_schools:
        print(f" - {name}: {cnt}")


def print_processed_table(processed: List[Dict[str, Any]], id_field: str = None, school_field: str = None) -> None:
    """Imprime tabla limpia con columnas: id, colegio, promedio."""
    print("\nCALIFICACIONES PROCESADAS:")
    headers = [h for h in (id_field, school_field) if h]
    headers += ["_average"]
    # imprimir cabecera
    print(" | ".join(headers))
    print("-" * (len(headers) * 12))
    for r in processed:
        parts = []
        for h in headers:
            v = r.get(h, "")
            parts.append(str(v) if v is not None else "")
        print(" | ".join(parts))


def main(path: str) -> None:
    rows = read_data(path)
    rows, warnings = validate_records(rows)
    print_warnings(warnings)

    summary_info = summary(rows)
    print_summary(summary_info)

    processed = process_grades(rows)
    # intentar inferir campos id y colegio para presentar
    id_field = None
    school_field = None
    if rows:
        headers = list(rows[0].keys())
        for h in headers:
            if h.lower().strip() in ("id", "identidad", "documento", "dni", "cedula"):
                id_field = h
                break
        for h in headers:
            if "coleg" in h.lower() or "escuel" in h.lower():
                school_field = h
                break

    print_processed_table(processed, id_field=id_field, school_field=school_field)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.merger <ruta_al_csv_o_xlsx>")
        sys.exit(1)
    main(sys.argv[1])
