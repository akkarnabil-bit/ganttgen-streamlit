# core/parser.py
import io
from typing import Union

import pandas as pd

# ---------------------------------------------------------------------------
# Column name normalisation maps
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {
    "tâche": "Tâche", "tache": "Tâche", "task": "Tâche",
    "début": "Début", "debut": "Début", "start": "Début", "date début": "Début",
    "fin": "Fin", "end": "Fin", "date fin": "Fin",
    "responsable": "Responsable", "assigné": "Responsable", "owner": "Responsable",
    "statut": "Statut", "status": "Statut", "état": "Statut",
}

OPTIONAL_COLUMNS = {
    "catégorie": "Catégorie", "categorie": "Catégorie", "category": "Catégorie",
    "avancement": "Avancement", "progress": "Avancement", "%": "Avancement",
}

MANDATORY_NORMALIZED = {"Tâche", "Début", "Fin", "Responsable", "Statut"}


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when the uploaded file cannot be turned into a valid DataFrame."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in REQUIRED_COLUMNS:
            mapping[col] = REQUIRED_COLUMNS[key]
        elif key in OPTIONAL_COLUMNS:
            mapping[col] = OPTIONAL_COLUMNS[key]
    return df.rename(columns=mapping)


def _check_required_columns(df: pd.DataFrame) -> None:
    missing = MANDATORY_NORMALIZED - set(df.columns)
    if missing:
        raise ValidationError(
            f"Colonnes manquantes : {', '.join(sorted(missing))}"
        )


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("Début", "Fin"):
        try:
            df[col] = pd.to_datetime(df[col], dayfirst=True)
        except Exception:
            raise ValidationError(
                f"La colonne '{col}' contient des dates invalides."
            )
    return df


def _validate_dates(df: pd.DataFrame) -> None:
    invalid = df[df["Fin"] < df["Début"]]
    if not invalid.empty:
        raise ValidationError(
            f"Date de fin avant début pour : {invalid['Tâche'].tolist()}"
        )


def _fill_optional(df: pd.DataFrame) -> pd.DataFrame:
    if "Catégorie" not in df.columns:
        df["Catégorie"] = "Général"
    if "Avancement" not in df.columns:
        df["Avancement"] = 0
    else:
        df["Avancement"] = (
            pd.to_numeric(df["Avancement"], errors="coerce")
            .fillna(0)
            .clip(0, 100)
            .astype(int)
        )
    return df


def _finalise(df: pd.DataFrame) -> pd.DataFrame:
    """Common post-processing shared by both parsers."""
    df["Tâche"]       = df["Tâche"].astype(str).str.strip()
    df["Responsable"] = df["Responsable"].astype(str).str.strip()
    df["Statut"]      = df["Statut"].astype(str).str.strip()
    df = df.dropna(subset=["Tâche", "Début", "Fin"])
    df = df.sort_values("Début").reset_index(drop=True)
    return df


def _build_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and enrich a raw DataFrame regardless of its source format."""
    if df.empty:
        raise ValidationError("Le fichier est vide.")

    df = _normalize_columns(df)
    _check_required_columns(df)
    df = _parse_dates(df)
    _validate_dates(df)
    df = _fill_optional(df)
    df = _finalise(df)
    return df


# ---------------------------------------------------------------------------
# Public parsers
# ---------------------------------------------------------------------------

def parse_excel(file: Union[str, io.BytesIO]) -> pd.DataFrame:
    """Read an .xlsx file and return a validated DataFrame."""
    try:
        df = pd.read_excel(file, engine="openpyxl")
    except Exception as e:
        raise ValidationError(f"Impossible de lire le fichier Excel : {e}")

    return _build_df(df)


def parse_csv(file: Union[str, io.BytesIO]) -> pd.DataFrame:
    """
    Read a .csv file and return a validated DataFrame.
    Tries common separators and encodings automatically.
    """
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        for sep in (",", ";", "\t"):
            try:
                if hasattr(file, "seek"):
                    file.seek(0)
                df = pd.read_csv(file, sep=sep, encoding=encoding)
                if len(df.columns) > 1:
                    return _build_df(df)
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
            except Exception as e:
                raise ValidationError(f"Impossible de lire le fichier CSV : {e}")

    raise ValidationError(
        "Impossible de détecter le séparateur ou l'encodage du fichier CSV. "
        "Essaie de l'enregistrer en UTF-8 avec des virgules comme séparateur."
    )


def parse_file(file) -> pd.DataFrame:
    """
    Dispatch to the right parser based on the uploaded file's name.
    Accepts both .xlsx and .csv files.
    """
    name = getattr(file, "name", "")
    if name.lower().endswith(".csv"):
        return parse_csv(file)
    elif name.lower().endswith(".xlsx"):
        return parse_excel(file)
    else:
        raise ValidationError(
            "Format non supporté. Importe un fichier .xlsx ou .csv."
        )