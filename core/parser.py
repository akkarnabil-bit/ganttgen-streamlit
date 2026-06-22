import pandas as pd
from typing import Union
import io

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


class ValidationError(Exception):
    pass


def _normalize_columns(df):
    mapping = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in REQUIRED_COLUMNS:
            mapping[col] = REQUIRED_COLUMNS[key]
        elif key in OPTIONAL_COLUMNS:
            mapping[col] = OPTIONAL_COLUMNS[key]
    return df.rename(columns=mapping)


def _check_required_columns(df):
    missing = MANDATORY_NORMALIZED - set(df.columns)
    if missing:
        raise ValidationError(f"Colonnes manquantes : {', '.join(sorted(missing))}")


def _parse_dates(df):
    for col in ("Début", "Fin"):
        try:
            df[col] = pd.to_datetime(df[col], dayfirst=True)
        except Exception:
            raise ValidationError(f"La colonne '{col}' contient des dates invalides.")
    return df


def _validate_dates(df):
    invalid = df[df["Fin"] < df["Début"]]
    if not invalid.empty:
        raise ValidationError(f"Date de fin avant début pour : {invalid['Tâche'].tolist()}")


def _fill_optional(df):
    if "Catégorie" not in df.columns:
        df["Catégorie"] = "Général"
    if "Avancement" not in df.columns:
        df["Avancement"] = 0
    else:
        df["Avancement"] = pd.to_numeric(df["Avancement"], errors="coerce").fillna(0).clip(0, 100).astype(int)
    return df


def parse_excel(file: Union[str, io.BytesIO]) -> pd.DataFrame:
    try:
        df = pd.read_excel(file, engine="openpyxl")
    except Exception as e:
        raise ValidationError(f"Impossible de lire le fichier Excel : {e}")

    if df.empty:
        raise ValidationError("Le fichier Excel est vide.")

    df = _normalize_columns(df)
    _check_required_columns(df)
    df = _parse_dates(df)
    _validate_dates(df)
    df = _fill_optional(df)

    df["Tâche"] = df["Tâche"].astype(str).str.strip()
    df["Responsable"] = df["Responsable"].astype(str).str.strip()
    df["Statut"] = df["Statut"].astype(str).str.strip()
    df = df.dropna(subset=["Tâche", "Début", "Fin"])
    df = df.sort_values("Début").reset_index(drop=True)

    return df