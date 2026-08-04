import os
import re
import unicodedata
from io import BytesIO

import pandas as pd
import streamlit as st

DEFAULT_CSV_CANDIDATES = [
    os.path.join("Data", "Inscripción", "INFORMACION GENERAL ESTUDIANTES INSCRITOS ORM 2026 - Hoja 1.csv"),
    os.path.join("Data", "processed", "cleaned_dashboard.csv"),
]
SUPPORTED_TYPES = ["csv", "xlsx", "xls"]

DEPARTMENT_MAP = {
    "antioquia": "Antioquia",
    "atlantico": "Atlántico",
    "bolivar": "Bolívar",
    "boyaca": "Boyacá",
    "caldas": "Caldas",
    "caqueta": "Caquetá",
    "cauca": "Cauca",
    "cesar": "Cesar",
    "choco": "Chocó",
    "cordoba": "Córdoba",
    "cundinamarca": "Cundinamarca",
    "guainia": "Guainía",
    "guaviare": "Guaviare",
    "huila": "Huila",
    "la guajira": "La Guajira",
    "magdalena": "Magdalena",
    "meta": "Meta",
    "narino": "Nariño",
    "norte de santander": "Norte de Santander",
    "putumayo": "Putumayo",
    "quindio": "Quindío",
    "risaralda": "Risaralda",
    "santander": "Santander",
    "sucre": "Sucre",
    "tolima": "Tolima",
    "valle del cauca": "Valle del Cauca",
    "valle": "Valle del Cauca",
    "valle del cauca ": "Valle del Cauca",
    "vaupes": "Vaupés",
    "amazonas": "Amazonas",
    "archipielago de san andres providencia y santa catalina": "Archipiélago de San Andrés, Providencia y Santa Catalina",
    "san andres": "Archipiélago de San Andrés, Providencia y Santa Catalina",
}

MUNICIPALITY_MAP = {
    "cali": "Cali",
    "santiago de cali": "Cali",
    "bogota": "Bogotá",
    "bogotá": "Bogotá",
    "bogota d c": "Bogotá",
    "medellin": "Medellín",
    "medellín": "Medellín",
    "barranquilla": "Barranquilla",
    "cartagena": "Cartagena",
    "bucaramanga": "Bucaramanga",
    "pereira": "Pereira",
    "manizales": "Manizales",
    "ibague": "Ibagué",
    "ibagué": "Ibagué",
    "armenia": "Armenia",
    "pasto": "Pasto",
    "popayan": "Popayán",
    "popayán": "Popayán",
    "villavicencio": "Villavicencio",
    "monteria": "Montería",
    "montería": "Montería",
    "sincelejo": "Sincelejo",
    "neiva": "Neiva",
    "tunja": "Tunja",
    "floridablanca": "Floridablanca",
    "soacha": "Soacha",
    "soledad": "Soledad",
    "malaga": "Malaga",
    "cartago": "Cartago",
    "buga": "Buga",
    "tulua": "Tulúa",
    "tuluá": "Tulúa",
    "palmira": "Palmira",
    "jamundi": "Jamundí",
    "jamundí": "Jamundí",
}

SCHOOL_MAP = {
    "ie gabo": "IE Gabo",
    "institucion educativa gabo": "IE Gabo",
    "institucion educativa agricola zaragoza": "Institución Educativa Agrícola Zaragoza",
    "colegio tecnico vicente azuero": "Colegio Técnico Vicente Azuero",
    "colegio tecnico": "Colegio Técnico",
    "liceo patria": "Liceo Patria",
    "colegio san jose": "Colegio San José",
    "colegio san josé": "Colegio San José",
}

st.set_page_config(page_title="Dashboard Olimpiadas", layout="wide")


def normalize_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def find_column(df, candidates):
    if df.empty:
        return None
    normalized_lookup = {normalize_text(col): col for col in df.columns}
    for candidate in candidates:
        if normalize_text(candidate) in normalized_lookup:
            return normalized_lookup[normalize_text(candidate)]
    for col in df.columns:
        col_norm = normalize_text(col)
        for candidate in candidates:
            if normalize_text(candidate) in col_norm:
                return col
    return None


def canonicalize_value(value, mapping):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    normalized_key = normalize_text(text)
    if normalized_key in mapping:
        return mapping[normalized_key]
    return text.strip()


def clean_place_value(value, mapping):
    cleaned = canonicalize_value(value, mapping)
    if cleaned:
        return cleaned.title()
    return ""


@st.cache_data
def load_data(path=None, uploaded_file=None):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                return pd.read_csv(uploaded_file, dtype=str)
            return pd.read_excel(uploaded_file, dtype=str)
        except ImportError as exc:
            st.error(f"No se pudo leer el archivo Excel. Instala openpyxl en tu entorno: {exc}")
            return pd.DataFrame()
        except Exception as exc:
            st.error(f"No se pudo leer el archivo: {exc}")
            return pd.DataFrame()

    return pd.DataFrame()


def add_school_type_column(df):
    df = df.copy()
    tipo_col = find_column(df, ["Sector", "tipo de colegio", "tipo_colegio", "tipo", "modalidad", "caracter", "publico_privado"])

    if tipo_col is None:
        df["tipo_colegio"] = "No definido"
        return df

    def classify_tipo(value):
        text = normalize_text(value)
        if not text:
            return "No definido"

        if text in {"publico", "publica", "oficial", "sector publico", "institucion publica", "instituto publico"}:
            return "Público"

        if text in {"privado no cobertura", "privado en cobertura", "privado", "privada", "particular", "sector privado", "institucion privada", "instituto privado", "no oficial", "no oficialidad"}:
            return "Privado"

        if text == "individual":
            return "No definido"

        if "publico" in text:
            return "Público"

        if "privado" in text:
            return "Privado"

        return "No definido"

    df["tipo_colegio"] = df[tipo_col].apply(classify_tipo)
    return df


def add_gender_column(df):
    df = df.copy()
    gender_col = find_column(df, ["genero", "sexo", "gender"])

    if gender_col is None:
        df["genero_normalizado"] = "No definido"
        return df

    def normalize_gender(value):
        text = normalize_text(value)
        if text in {"m", "masculino", "male", "hombre"}:
            return "Hombre"
        if text in {"f", "femenino", "female", "mujer"}:
            return "Mujer"
        return "Otro / No definido"

    df["genero_normalizado"] = df[gender_col].apply(normalize_gender)
    return df


def normalize_levels(df):
    df = df.copy()
    level_col = find_column(df, ["Nivel", "Nivel (junio,basico, medio o avanzado)", "nivel", "grado", "Grado", "level"])
    if level_col is None:
        df["_level_normalized"] = "No definido"
        df["_grado_numero"] = ""
        return df

    def normalize_level(value):
        text = normalize_text(value)
        if not text:
            return "No definido"

        if any(token in text for token in ["junior", "juniors", "cuarto", "quinto", "4to", "5to", "4", "5"]):
            return "Junior"
        if any(token in text for token in ["basico", "basico", "sexto", "septimo", "6to", "7mo", "7to", "6", "7"]):
            return "Básico"
        if any(token in text for token in ["medio", "octavo", "noveno", "8vo", "9no", "9vo", "8", "9"]):
            return "Medio"
        if any(token in text for token in ["avanzado", "decimo", "once", "10mo", "11vo", "10", "11"]):
            return "Avanzado"

        return "No definido"

    def normalize_grade_number(value):
        text = str(value).strip()
        if not text:
            return ""
        match = re.search(r"(\d+)", text)
        if match:
            return match.group(1)
        return ""

    df["_level_normalized"] = df[level_col].apply(normalize_level)
    df["_grado_numero"] = df[level_col].apply(normalize_grade_number)
    df["Grado"] = df["_grado_numero"]
    df["Nivel"] = df["_level_normalized"]
    return df


def apply_name_normalization(df, school_col, dept_col, mun_col):
    df = df.copy()
    if dept_col:
        df["Departamento"] = df[dept_col].apply(lambda value: clean_place_value(value, DEPARTMENT_MAP))
    else:
        df["Departamento"] = ""

    if mun_col:
        df["Municipio"] = df[mun_col].apply(lambda value: clean_place_value(value, MUNICIPALITY_MAP))
    else:
        df["Municipio"] = ""

    if school_col:
        df["Nombre del colegio o institución educativa"] = df[school_col].apply(lambda value: canonicalize_value(value, SCHOOL_MAP))
    else:
        df["Nombre del colegio o institución educativa"] = ""

    for col in df.columns:
        col_norm = normalize_text(col)
        if (
            ("nombre" in col_norm or "apellido" in col_norm)
            and "colegio" not in col_norm
            and "institucion" not in col_norm
            and "educativa" not in col_norm
        ):
            df[col] = df[col].apply(lambda value: str(value).strip().upper() if pd.notna(value) and str(value).strip() else "")

    return df


def detect_problems(df):
    names_col = find_column(df, ["nombres", "nombre", "nombres completos"])
    surnames_col = find_column(df, ["apellidos", "apellido"])
    id_col = find_column(df, ["numero identificacion", "identificacion", "numero de identificacion", "id", "numeroidentificacion"])
    dept_col = find_column(df, ["departamento", "departamento residencia"])
    mun_col = find_column(df, ["municipio", "municipio residencia"])

    def empty_series(series):
        return series.isna() | (series.astype(str).str.strip() == "")

    rows_with_errors = []
    for idx, row in df.iterrows():
        reasons = []
        if names_col and empty_series(pd.Series([row[names_col]]))[0]:
            reasons.append("Nombre faltante")
        if surnames_col and empty_series(pd.Series([row[surnames_col]]))[0]:
            reasons.append("Apellido faltante")
        if id_col:
            id_value = str(row[id_col]).strip()
            if not id_value:
                reasons.append("ID faltante")
            elif not re.fullmatch(r"\d+", id_value):
                reasons.append("ID no numérico")
        if dept_col and not str(row[dept_col]).strip():
            reasons.append("Departamento faltante")
        if mun_col and not str(row[mun_col]).strip():
            reasons.append("Municipio faltante")

        if reasons:
            new_row = row.to_dict()
            new_row["error"] = "; ".join(reasons)
            rows_with_errors.append(new_row)

    if not rows_with_errors:
        return pd.DataFrame(columns=[*df.columns, "error"])

    return pd.DataFrame(rows_with_errors)


def main():
    st.header("Carga de archivo")
    st.caption("Sube un archivo CSV/Excel para comenzar. Mientras no exista un archivo, la vista permanecerá en blanco.")
    uploaded_file = st.file_uploader("Subir archivo CSV/Excel", type=SUPPORTED_TYPES, key="main_uploader")

    if uploaded_file is None:
        st.info("Aún no hay archivo cargado. Sube uno desde arriba para empezar.")
        return

    st.title("Dashboard - Inscripciones Olimpiadas")
    df = load_data(uploaded_file=uploaded_file)

    if df.empty:
        st.info("No se pudo leer el archivo cargado. Intenta con otro archivo.")
        return

    df = add_school_type_column(df)
    df = add_gender_column(df)
    df = normalize_levels(df)

    school_col = find_column(df, ["nombre del colegio o institucion educativa", "nombre del colegio", "colegio", "institucion educativa"])
    dept_col = find_column(df, ["departamento"])
    mun_col = find_column(df, ["municipio"])
    level_col = find_column(df, ["_level_normalized", "nivel", "grado", "level"])
    if level_col is None:
        level_col = find_column(df, ["grado", "nivel"])

    if school_col is None:
        school_col = df.columns[0]
    if dept_col is None:
        dept_col = "Departamento"
    if mun_col is None:
        mun_col = "Municipio"
    if level_col is None:
        level_col = df.columns[0]

    df = apply_name_normalization(df, school_col, dept_col, mun_col)
    df["_level_normalized"] = df["_level_normalized"].fillna("").astype(str).str.strip()
    df["_grado_numero"] = df["_grado_numero"].fillna("").astype(str).str.strip()
    df["Grado"] = df["_grado_numero"]
    df["Nivel"] = df["_level_normalized"]

    st.sidebar.header("Filtros")
    dept_options = ["(Todos)"] + sorted(df["Departamento"].dropna().unique().tolist())
    sel_dept = st.sidebar.selectbox("Departamento", dept_options)
    if sel_dept != "(Todos)":
        df = df[df["Departamento"] == sel_dept]

    mun_options = ["(Todos)"] + sorted(df["Municipio"].dropna().unique().tolist())
    sel_mun = st.sidebar.selectbox("Municipio", mun_options)
    if sel_mun != "(Todos)":
        df = df[df["Municipio"] == sel_mun]

    school_options = ["(Todos)"] + sorted(df["Nombre del colegio o institución educativa"].dropna().unique().tolist())
    sel_school = st.sidebar.selectbox("Colegio", school_options)
    if sel_school != "(Todos)":
        df = df[df["Nombre del colegio o institución educativa"] == sel_school]

    level_options = ["(Todos)"] + sorted(df["_level_normalized"].dropna().unique().tolist())
    sel_level = st.sidebar.selectbox("Nivel", level_options)
    if sel_level != "(Todos)":
        df = df[df["_level_normalized"] == sel_level]

    tipo_options = ["(Todos)"] + sorted(df["tipo_colegio"].dropna().unique().tolist())
    sel_tipo = st.sidebar.selectbox("Tipo de colegio", tipo_options)
    if sel_tipo != "(Todos)":
        df = df[df["tipo_colegio"] == sel_tipo]

    gender_options = ["(Todos)"] + sorted(df["genero_normalizado"].dropna().unique().tolist())
    sel_gender = st.sidebar.selectbox("Género", gender_options)
    if sel_gender != "(Todos)":
        df = df[df["genero_normalizado"] == sel_gender]

    has_filters = any(
        selection not in {"(Todos)", "", None}
        for selection in [sel_dept, sel_mun, sel_school, sel_level, sel_tipo, sel_gender]
    )

    total = len(df)
    unique_schools = df["Nombre del colegio o institución educativa"].nunique()
    unique_departments = df["Departamento"].nunique()
    unique_municipalities = df["Municipio"].nunique()
    unique_levels = df["_level_normalized"].nunique()
    hombres = int((df["genero_normalizado"] == "Hombre").sum()) if "genero_normalizado" in df.columns else 0
    mujeres = int((df["genero_normalizado"] == "Mujer").sum()) if "genero_normalizado" in df.columns else 0
    privados = int((df["tipo_colegio"] == "Privado").sum()) if "tipo_colegio" in df.columns else 0
    publicos = int((df["tipo_colegio"] == "Público").sum()) if "tipo_colegio" in df.columns else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total registros", total)
    col2.metric("Colegios únicos", unique_schools)
    col3.metric("Departamentos", unique_departments)
    col4.metric("Municipios", unique_municipalities)
    col5.metric("Hombres", hombres)
    col6.metric("Mujeres", mujeres)

    col7, col8 = st.columns(2)
    col7.metric("Colegios privados", privados)
    col8.metric("Colegios públicos", publicos)

    if not has_filters:
        st.info("Sin filtros activos, la vista muestra solo métricas resumidas. Activa un filtro para ver distribuciones.")
    else:
        st.header("Distribuciones")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Por nivel")
            st.bar_chart(df["_level_normalized"].value_counts())
        with c2:
            st.subheader("Por municipio")
            st.bar_chart(df["Municipio"].value_counts().head(15))
        with c3:
            st.subheader("Por tipo de colegio")
            st.bar_chart(df["tipo_colegio"].value_counts())

        st.header("Estadísticas por género")
        gender_counts = df["genero_normalizado"].value_counts()
        st.bar_chart(gender_counts)

    st.header("Tabla de registros")
    st.dataframe(df, use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    excel_bytes = excel_buffer.getvalue()
    st.download_button("Descargar CSV filtrado", data=csv_bytes, file_name="dashboard_filtrado.csv", mime="text/csv")
    st.download_button("Descargar Excel filtrado", data=excel_bytes, file_name="dashboard_filtrado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    problems_df = detect_problems(df)
    st.subheader("Registros problemáticos")
    st.write(f"Total problemáticos: {len(problems_df)}")
    if not problems_df.empty:
        st.dataframe(problems_df.head(200), use_container_width=True)
        prob_csv = problems_df.to_csv(index=False).encode("utf-8")
        prob_excel_buffer = BytesIO()
        with pd.ExcelWriter(prob_excel_buffer, engine="openpyxl") as writer:
            problems_df.to_excel(writer, index=False, sheet_name="Problemas")
        prob_excel = prob_excel_buffer.getvalue()
        st.download_button("Exportar problems.csv", data=prob_csv, file_name="problems.csv", mime="text/csv")
        st.download_button("Exportar problems.xlsx", data=prob_excel, file_name="problems.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("---")
    st.caption("Puedes subir un archivo nuevo desde la barra lateral, filtrar por municipio y ver métricas por género y tipo de colegio.")


if __name__ == "__main__":
    main()
