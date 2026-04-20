"""
tests/test_entity_resolution.py
---------------------------------
Unit tests for sync/entity_resolution.py.

Tests cover:
  - normalize_company_name: legal suffix stripping, casing, whitespace
  - compute_similarity: basic ratio correctness and edge cases
  - resolve_entities: RUT-based grouping, name-based fuzzy grouping,
    synthetic key stability, confidence values
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.entity_resolution import (
    normalize_company_name,
    compute_similarity,
    resolve_entities,
)


# ── normalize_company_name ─────────────────────────────────────────────────────

class TestNormalizeCompanyName:
    def test_strips_sa_suffix(self):
        assert normalize_company_name("Empresa Alimentos S.A.") == "empresa alimentos"

    def test_strips_sa_no_dots(self):
        assert normalize_company_name("Empresa Alimentos SA") == "empresa alimentos"

    def test_strips_ltda(self):
        assert normalize_company_name("Tech Startup Ltda") == "tech startup"

    def test_strips_limitada(self):
        assert normalize_company_name("Comercial Sur Limitada") == "comercial sur"

    def test_strips_spa(self):
        assert normalize_company_name("Innovacion Digital SpA") == "innovacion digital"

    def test_strips_eirl(self):
        assert normalize_company_name("Consultora Norte EIRL") == "consultora norte"

    def test_strips_eirl_with_dots(self):
        assert normalize_company_name("Servicios Ltda. E.I.R.L.") == "servicios"

    def test_lowercases_result(self):
        result = normalize_company_name("EMPRESA GRANDE S.A.")
        assert result == result.lower()

    def test_collapses_internal_whitespace(self):
        assert normalize_company_name("Empresa   con  Espacios") == "empresa con espacios"

    def test_handles_empty_string(self):
        assert normalize_company_name("") == ""

    def test_handles_none(self):
        assert normalize_company_name(None) == ""

    def test_no_suffix_unchanged_except_case(self):
        assert normalize_company_name("Universidad de Chile") == "universidad de chile"

    def test_strips_trailing_whitespace_before_suffix(self):
        # "S.A." after extra spaces should still be stripped
        assert normalize_company_name("Empresa Alimentos  S.A.") == "empresa alimentos"

    def test_only_suffix_returns_empty(self):
        # Edge case: name is just a legal suffix
        result = normalize_company_name("S.A.")
        assert result == ""


# ── compute_similarity ────────────────────────────────────────────────────────

class TestComputeSimilarity:
    def test_identical_strings_return_one(self):
        assert compute_similarity("empresa alimentos", "empresa alimentos") == 1.0

    def test_empty_a_returns_zero(self):
        assert compute_similarity("", "empresa alimentos") == 0.0

    def test_empty_b_returns_zero(self):
        assert compute_similarity("empresa alimentos", "") == 0.0

    def test_both_empty_returns_zero(self):
        assert compute_similarity("", "") == 0.0

    def test_similar_names_above_threshold(self):
        # "empresa alimentos" vs "empresa de alimentos" should be highly similar
        sim = compute_similarity("empresa alimentos", "empresa de alimentos")
        assert sim >= 0.85

    def test_completely_different_names_below_threshold(self):
        sim = compute_similarity("fruta del campo", "tecnologia digital")
        assert sim < 0.5

    def test_same_name_different_case_normalized(self):
        # Expects pre-normalized input (both already lowercased)
        a = normalize_company_name("Empresa Alimentos S.A.")
        b = normalize_company_name("Empresa Alimentos SA")
        assert compute_similarity(a, b) == 1.0


# ── resolve_entities ──────────────────────────────────────────────────────────

class TestResolveEntities:
    def _make_df(self, rows: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(rows)

    def test_rut_rows_get_confidence_one(self):
        df = self._make_df([
            {"rut_beneficiario": "12345678-9", "razon": "Empresa A S.A."},
            {"rut_beneficiario": "98765432-1", "razon": "Empresa B Ltda"},
        ])
        result = resolve_entities(df)
        assert list(result["match_confidence"]) == [1.0, 1.0]

    def test_rut_rows_use_rut_as_canonical(self):
        df = self._make_df([
            {"rut_beneficiario": "12345678-9", "razon": "Empresa A S.A."},
        ])
        result = resolve_entities(df)
        assert result.iloc[0]["canonical_rut"] == "12345678-9"

    def test_null_rut_singleton_gets_synthetic_key(self):
        df = self._make_df([
            {"rut_beneficiario": None, "razon": "Empresa Sin Rut S.A."},
        ])
        result = resolve_entities(df)
        key = result.iloc[0]["canonical_rut"]
        assert key.startswith("NOTIN-")

    def test_null_rut_singleton_confidence_is_zero(self):
        df = self._make_df([
            {"rut_beneficiario": None, "razon": "Empresa Solitaria"},
        ])
        result = resolve_entities(df)
        assert result.iloc[0]["match_confidence"] == 0.0

    def test_fuzzy_matched_null_rut_rows_share_canonical_key(self):
        df = self._make_df([
            {"rut_beneficiario": None, "razon": "Empresa Alimentos S.A."},
            {"rut_beneficiario": None, "razon": "Empresa Alimentos SA"},
            {"rut_beneficiario": "", "razon": "Empresa Alimentos"},
        ])
        result = resolve_entities(df)
        keys = result["canonical_rut"].tolist()
        # All three should resolve to the same canonical_rut
        assert keys[0] == keys[1] == keys[2]

    def test_fuzzy_matched_confidence_above_threshold(self):
        df = self._make_df([
            {"rut_beneficiario": None, "razon": "Empresa Alimentos S.A."},
            {"rut_beneficiario": None, "razon": "Empresa Alimentos SA"},
        ])
        result = resolve_entities(df)
        assert result.iloc[0]["match_confidence"] >= 0.85
        assert result.iloc[1]["match_confidence"] >= 0.85

    def test_rut_company_not_merged_with_null_rut_company(self):
        """A company with a known RUT must never be merged with a null-RUT company."""
        df = self._make_df([
            {"rut_beneficiario": "12345678-9", "razon": "Empresa Alimentos S.A."},
            {"rut_beneficiario": None,          "razon": "Empresa Alimentos SA"},
        ])
        result = resolve_entities(df)
        # The RUT row keeps its own RUT as canonical_rut
        assert result.iloc[0]["canonical_rut"] == "12345678-9"
        # The null-RUT row gets a synthetic key, not the RUT
        assert result.iloc[1]["canonical_rut"] != "12345678-9"
        assert result.iloc[1]["canonical_rut"].startswith("NOTIN-")

    def test_empty_name_null_rut_gets_synthetic_key(self):
        df = self._make_df([
            {"rut_beneficiario": None, "razon": ""},
        ])
        result = resolve_entities(df)
        key = result.iloc[0]["canonical_rut"]
        assert key.startswith("NOTIN-")
        assert result.iloc[0]["match_confidence"] == 0.0

    def test_synthetic_key_is_stable_for_same_name(self):
        """Same name must always produce the same synthetic key."""
        df1 = self._make_df([{"rut_beneficiario": None, "razon": "Empresa Test"}])
        df2 = self._make_df([{"rut_beneficiario": None, "razon": "Empresa Test"}])
        r1 = resolve_entities(df1)
        r2 = resolve_entities(df2)
        assert r1.iloc[0]["canonical_rut"] == r2.iloc[0]["canonical_rut"]

    def test_output_has_canonical_rut_and_match_confidence_columns(self):
        df = self._make_df([
            {"rut_beneficiario": "11111111-1", "razon": "Alguna Empresa S.A."},
        ])
        result = resolve_entities(df)
        assert "canonical_rut" in result.columns
        assert "match_confidence" in result.columns

    def test_original_columns_preserved(self):
        df = self._make_df([
            {"rut_beneficiario": "11111111-1", "razon": "Empresa X"},
        ])
        result = resolve_entities(df)
        assert "rut_beneficiario" in result.columns
        assert "razon" in result.columns

    def test_different_unrelated_null_rut_companies_get_different_keys(self):
        df = self._make_df([
            {"rut_beneficiario": None, "razon": "Fruta del Campo Ltda"},
            {"rut_beneficiario": None, "razon": "Tecnologia Digital SA"},
        ])
        result = resolve_entities(df)
        assert result.iloc[0]["canonical_rut"] != result.iloc[1]["canonical_rut"]

    def test_empty_dataframe_returns_empty_with_new_columns(self):
        df = pd.DataFrame(columns=["rut_beneficiario", "razon"])
        result = resolve_entities(df)
        assert "canonical_rut" in result.columns
        assert "match_confidence" in result.columns
        assert len(result) == 0
