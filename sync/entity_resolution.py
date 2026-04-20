"""
sync/entity_resolution.py
--------------------------
Entity resolution for company names in the proyectos table.

Estrategia de resolución (dos niveles):
  1. RUT-based (confianza 1.0): mismo rut_beneficiario → misma empresa.
     Esto ya era el comportamiento de rebuild_empresas().
  2. Name-based fuzzy (confianza 0.85–1.0): para filas con rut_beneficiario
     NULL o vacío, normalizar el nombre y agrupar por similitud ≥ threshold.
     Se asigna un canonical_rut sintético "NOTIN-{hash}" estable por clúster.

Constraints:
  - No nuevas dependencias externas: solo difflib (stdlib)
  - Las empresas con RUT conocido nunca se fusionan con empresas sin RUT
  - O(n²) sobre el subconjunto sin RUT — aceptable para ~1500 filas
"""

import hashlib
import logging
import re
from difflib import SequenceMatcher

import pandas as pd

log = logging.getLogger("corfo.sync")

# Sufijos legales chilenos a eliminar en la normalización
_LEGAL_SUFFIXES = [
    r"e\.i\.r\.l\.",
    r"eirl",
    r"s\.a\.s\.",
    r"s\.p\.a\.",
    r"spa",
    r"s\.a\.",
    r"sa",
    r"ltda\.",
    r"ltda",
    r"limitada",
]

# Patrón que coincide con cualquier sufijo legal al final del string (ignorando espacios)
_SUFFIX_PATTERN = re.compile(
    r"\s*(?:" + "|".join(_LEGAL_SUFFIXES) + r")\s*$",
    re.IGNORECASE,
)


def normalize_company_name(name: str) -> str:
    """
    Strip legal suffixes, lowercase, and collapse whitespace.

    Pasos:
      1. Convertir a minúsculas
      2. Eliminar sufijos legales chilenos (s.a., ltda, spa, eirl, etc.)
         Aplica repetidamente hasta que no queden más sufijos
      3. Colapsar espacios múltiples y quitar espacios al inicio/fin

    Returns an empty string if name is empty or None-like after normalization.
    """
    if not name or not isinstance(name, str):
        return ""

    normalized = name.lower().strip()

    # Remove legal suffixes iteratively (a name may have stacked suffixes)
    prev = None
    while prev != normalized:
        prev = normalized
        normalized = _SUFFIX_PATTERN.sub("", normalized).strip()

    # Collapse internal whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def compute_similarity(a: str, b: str) -> float:
    """
    SequenceMatcher ratio between two normalized names.

    Expects already-normalized inputs (call normalize_company_name() first).
    Returns 0.0 if either string is empty.
    """
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _stable_synthetic_key(name: str) -> str:
    """Generate a stable synthetic canonical_rut for null-RUT companies."""
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()[:12]
    return f"NOTIN-{digest}"


def resolve_entities(
    df: pd.DataFrame,
    rut_col: str = "rut_beneficiario",
    name_col: str = "razon",
    threshold: float = 0.85,
) -> pd.DataFrame:
    """
    Add two columns to df:
      - canonical_rut: RUT to use for grouping.
          * For rows with a non-null/non-empty RUT: the RUT itself (confidence 1.0).
          * For rows with null/empty RUT: a synthetic "NOTIN-{hash}" key derived
            from the normalized name cluster (confidence 0.85–1.0 within cluster,
            or 0.0 if the name is blank).
      - match_confidence: confidence of the resolution.
          * 1.0  — resolved by RUT
          * 0.85–1.0 — resolved by name fuzzy match (cluster similarity)
          * 0.0  — unresolvable (empty name, no RUT)

    Empresas with known RUTs are NEVER merged with null-RUT rows, even if
    their names are similar.

    Returns a copy of df with the two new columns appended.
    """
    df = df.copy()

    # Initialize output columns
    df["canonical_rut"] = ""
    df["match_confidence"] = 0.0

    # ── Paso 1: filas con RUT conocido ────────────────────────────────────────
    has_rut_mask = (
        df[rut_col].notna()
        & (df[rut_col].astype(str).str.strip() != "")
    )
    df.loc[has_rut_mask, "canonical_rut"] = df.loc[has_rut_mask, rut_col].astype(str).str.strip()
    df.loc[has_rut_mask, "match_confidence"] = 1.0

    log.info(
        "Entity resolution: %d rows have known RUT (confidence 1.0)",
        int(has_rut_mask.sum()),
    )

    # ── Paso 2: filas sin RUT — resolución por nombre fuzzy ──────────────────
    no_rut_idx = df.index[~has_rut_mask].tolist()

    if not no_rut_idx:
        log.info("Entity resolution: no null-RUT rows to process")
        return df

    # Normalize names for all null-RUT rows
    names_raw = df.loc[no_rut_idx, name_col].fillna("").astype(str).tolist()
    names_norm = [normalize_company_name(n) for n in names_raw]

    # Union-Find to cluster similar names (O(n²) over null-RUT subset only)
    parent = list(range(len(no_rut_idx)))

    def _find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression
            x = parent[x]
        return x

    def _union(x: int, y: int) -> None:
        px, py = _find(x), _find(y)
        if px != py:
            parent[px] = py

    # Cluster similarity (only compare non-empty normalized names)
    for i in range(len(no_rut_idx)):
        if not names_norm[i]:
            continue
        for j in range(i + 1, len(no_rut_idx)):
            if not names_norm[j]:
                continue
            sim = compute_similarity(names_norm[i], names_norm[j])
            if sim >= threshold:
                _union(i, j)

    # Assign canonical_rut and confidence per cluster
    # Confidence for a fuzzy-matched cluster = average pairwise similarity
    # within the cluster. For singleton clusters (no match), confidence = 0.0
    # unless the name is non-empty, in which case it gets a stable solo key with 0.0.

    # Build cluster map: root_idx → list of member indices
    clusters: dict[int, list[int]] = {}
    for i in range(len(no_rut_idx)):
        root = _find(i)
        clusters.setdefault(root, []).append(i)

    for root, members in clusters.items():
        # Choose canonical name: first non-empty normalized name in cluster
        # (members are in original DataFrame order)
        cluster_norm_names = [names_norm[m] for m in members if names_norm[m]]

        if not cluster_norm_names:
            # All names empty — unresolvable.
            # Use raw razon + codigo as a content-stable seed so that the same
            # row gets the same synthetic key regardless of DataFrame row order.
            # If codigo is not in the DataFrame, fall back to raw razon alone
            # (two rows with the same empty razon merge — acceptable, they are
            # indistinguishable).
            for m in members:
                df_idx = no_rut_idx[m]
                row = df.loc[df_idx]
                raw_razon = str(row.get("razon", "") or "")
                if "codigo" in df.columns:
                    seed = f"__empty__{raw_razon}_{row['codigo']}__"
                else:
                    seed = f"__empty__{raw_razon}__"
                df.loc[df_idx, "canonical_rut"] = _stable_synthetic_key(seed)
                df.loc[df_idx, "match_confidence"] = 0.0
            continue

        canonical_name = cluster_norm_names[0]
        synthetic_key = _stable_synthetic_key(canonical_name)

        if len(members) == 1:
            # Singleton — no fuzzy match found; assign stable key, confidence 0.0
            df_idx = no_rut_idx[members[0]]
            df.loc[df_idx, "canonical_rut"] = synthetic_key
            df.loc[df_idx, "match_confidence"] = 0.0
        else:
            # Multi-member cluster — compute average pairwise similarity as confidence
            norm_names_in_cluster = [names_norm[m] for m in members]
            pairs = [
                compute_similarity(norm_names_in_cluster[i], norm_names_in_cluster[j])
                for i in range(len(members))
                for j in range(i + 1, len(members))
                if norm_names_in_cluster[i] and norm_names_in_cluster[j]
            ]
            confidence = sum(pairs) / len(pairs) if pairs else threshold

            for m in members:
                df_idx = no_rut_idx[m]
                df.loc[df_idx, "canonical_rut"] = synthetic_key
                df.loc[df_idx, "match_confidence"] = round(confidence, 4)

    null_rut_count = len(no_rut_idx)
    matched_count = sum(
        1 for root, members in clusters.items()
        if len(members) > 1
        for _ in members
    )
    log.info(
        "Entity resolution: %d null-RUT rows processed, %d matched into fuzzy clusters",
        null_rut_count,
        matched_count,
    )

    return df
