"""Accès au jeu de démonstration df_Test_Indust.csv (2024-S01→S39, 11 départements)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DEPARTEMENTS = {
    1: "Ain", 3: "Allier", 7: "Ardèche", 15: "Cantal", 26: "Drôme", 38: "Isère",
    42: "Loire", 43: "Haute-Loire", 69: "Rhône", 73: "Savoie", 74: "Haute-Savoie",
}


def week_cos(week: int) -> float:
    """Encodage cyclique utilisé à l'entraînement : cos(2π·semaine/52)."""
    return float(np.cos(2 * np.pi * week / 52))


def load_dataset(root: str | Path) -> pd.DataFrame:
    df = pd.read_csv(Path(root) / "df_Test_Indust.csv")
    # week_cos seul est ambigu : cos(2π·w/52) = cos(2π·(52-w)/52), donc S30 et S22 sont
    # indiscernables. Le fichier est trié chronologiquement par département (2024-S01→S39,
    # puis la ligne 2023-S52) : on reconstruit la semaine par le rang, puis on vérifie le cosinus.
    df["week"] = df.groupby(["dept", "year"]).cumcount() + 1
    df.loc[df["year"] == 2023, "week"] = 52
    expected = np.cos(2 * np.pi * df["week"] / 52)
    if not np.allclose(expected, df["week_cos"], atol=1e-9):
        raise ValueError("Ordre des semaines incohérent avec week_cos")
    return df


def lookup(df: pd.DataFrame, dept: int, year: int, week: int) -> dict | None:
    row = df[(df["dept"] == dept) & (df["year"] == year) & (df["week"] == week)]
    if row.empty:
        return None
    # conversion explicite en types Python natifs (sérialisation JSON)
    return {k: (int(v) if float(v).is_integer() and k in ("dept", "year", "week") else float(v))
            for k, v in row.iloc[0].items()}
