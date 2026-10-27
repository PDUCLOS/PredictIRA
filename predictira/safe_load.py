"""Chargement « sûr » des artefacts pickle hérités du projet.

pickle/joblib peuvent exécuter du code arbitraire au chargement. On n'autorise
donc que les classes réellement présentes dans les fichiers du dépôt (vérifiées
par désassemblage pickletools) : numpy, scikit-learn StandardScaler, LightGBM.
"""
from __future__ import annotations

import pickle

from joblib import numpy_pickle

ALLOWED = {
    ("collections", "OrderedDict"),
    ("collections", "defaultdict"),
    ("_codecs", "encode"),
    ("numpy", "dtype"),
    ("numpy", "ndarray"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy.core.multiarray", "scalar"),
    ("numpy._core.multiarray", "_reconstruct"),
    ("numpy._core.multiarray", "scalar"),
    ("joblib.numpy_pickle", "NumpyArrayWrapper"),
    ("sklearn.preprocessing._data", "StandardScaler"),
    ("lightgbm.basic", "Booster"),
    ("lightgbm.sklearn", "LGBMRegressor"),
}


class _AllowListUnpickler(numpy_pickle.NumpyUnpickler):
    def find_class(self, module, name):
        if (module, name) not in ALLOWED:
            raise pickle.UnpicklingError(f"classe interdite dans le pickle : {module}.{name}")
        return super().find_class(module, name)


def safe_joblib_load(path: str):
    """Équivalent de joblib.load restreint à la liste blanche ALLOWED."""
    with open(path, "rb") as fh:
        return _AllowListUnpickler(path, fh, ensure_native_byte_order="auto").load()
