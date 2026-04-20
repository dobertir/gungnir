"""
Inline unit tests for _is_numeric_value and determine_chart_type (DOB-101).

Extracts the two pure helper functions directly from corfo_server.py source
without importing the full Flask application.
"""
import sys
import os
import unittest

SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "corfo_server.py")

# ---------------------------------------------------------------------------
# Extract only the two helper functions from source — no Flask import needed
# ---------------------------------------------------------------------------
with open(SERVER_PATH, "r", encoding="utf-8") as fh:
    lines = fh.readlines()


def _extract_function_source(lines, func_name):
    """Return the source lines of a top-level function by name."""
    start = None
    for i, ln in enumerate(lines):
        if ln.rstrip().startswith(f"def {func_name}("):
            start = i
            break
    if start is None:
        raise RuntimeError(f"Function '{func_name}' not found in corfo_server.py")
    body = [lines[start]]
    for ln in lines[start + 1:]:
        # Stop at the next top-level definition or non-empty non-indented line
        if ln.strip() and not ln[0].isspace():
            break
        body.append(ln)
    return "".join(body)


fn_source = (
    _extract_function_source(lines, "_is_numeric_value")
    + "\n\n"
    + _extract_function_source(lines, "determine_chart_type")
)

fn_ns: dict = {}
exec(compile(fn_source, "extracted_helpers", "exec"), fn_ns)

_is_numeric_value = fn_ns["_is_numeric_value"]
determine_chart_type = fn_ns["determine_chart_type"]


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------
class TestIsNumericValue(unittest.TestCase):

    def test_integer_string(self):
        self.assertTrue(_is_numeric_value("1000"))

    def test_float_string(self):
        self.assertTrue(_is_numeric_value("3.14"))

    def test_actual_int(self):
        self.assertTrue(_is_numeric_value(42))

    def test_actual_float(self):
        self.assertTrue(_is_numeric_value(3.14))

    def test_non_numeric_string(self):
        self.assertFalse(_is_numeric_value("activo"))

    def test_none(self):
        self.assertFalse(_is_numeric_value(None))

    def test_empty_string(self):
        self.assertFalse(_is_numeric_value(""))

    def test_negative_number(self):
        self.assertTrue(_is_numeric_value("-500"))

    def test_scientific_notation(self):
        self.assertTrue(_is_numeric_value("1e6"))


class TestDetermineChartType(unittest.TestCase):

    # ── Six required cases from DOB-101 spec ────────────────────────────────

    def test_dob101_case1_line(self):
        """2 cols, first has 'año' → line"""
        cols = ["año_adjudicacion", "total"]
        rows = [["2020", "1000"], ["2021", "2000"]]
        self.assertEqual(determine_chart_type(cols, rows), "line")

    def test_dob101_case2_pie(self):
        """2 cols, categorical first, numeric second, ≤8 rows → pie"""
        cols = ["region", "count"]
        rows = [["Norte", "10"], ["Sur", "20"], ["Centro", "30"]]
        self.assertEqual(determine_chart_type(cols, rows), "pie")

    def test_dob101_case3_bar(self):
        """2 cols, categorical first, numeric second, >8 rows → bar"""
        cols = ["empresa", "monto"]
        rows = [["A", "1"]] * 10
        self.assertEqual(determine_chart_type(cols, rows), "bar")

    def test_dob101_case4_table_three_cols(self):
        """3 columns → table"""
        cols = ["empresa", "region", "monto"]
        rows = [["A", "B", "1"]]
        self.assertEqual(determine_chart_type(cols, rows), "table")

    def test_dob101_case5_table_one_col(self):
        """Single column → table"""
        cols = ["empresa"]
        rows = [["A"]]
        self.assertEqual(determine_chart_type(cols, rows), "table")

    def test_dob101_case6_table_zero_rows(self):
        """Zero rows → table"""
        cols = ["año", "total"]
        rows = []
        self.assertEqual(determine_chart_type(cols, rows), "table")

    # ── Dict-row format (as produced by df.to_dict(orient='records')) ───────

    def test_line_dict_rows(self):
        cols = ["año_adjudicacion", "total"]
        rows = [{"año_adjudicacion": "2020", "total": "1000"},
                {"año_adjudicacion": "2021", "total": "2000"}]
        self.assertEqual(determine_chart_type(cols, rows), "line")

    def test_pie_dict_rows(self):
        cols = ["region", "count"]
        rows = [{"region": "Norte", "count": "10"},
                {"region": "Sur", "count": "20"}]
        self.assertEqual(determine_chart_type(cols, rows), "pie")

    def test_bar_dict_rows_gt8(self):
        cols = ["empresa", "monto"]
        rows = [{"empresa": f"E{i}", "monto": str(i * 100)} for i in range(10)]
        self.assertEqual(determine_chart_type(cols, rows), "bar")

    def test_table_non_numeric_second_col(self):
        """Second column is non-numeric → table"""
        cols = ["empresa", "estado"]
        rows = [{"empresa": "A", "estado": "activo"},
                {"empresa": "B", "estado": "inactivo"}]
        self.assertEqual(determine_chart_type(cols, rows), "table")

    # ── Time-keyword variations ──────────────────────────────────────────────

    def test_line_fecha_keyword(self):
        cols = ["fecha_inicio", "proyectos"]
        rows = [["2023-01", "5"], ["2023-02", "8"]]
        self.assertEqual(determine_chart_type(cols, rows), "line")

    def test_line_mes_keyword(self):
        cols = ["mes", "ingresos"]
        rows = [["Enero", "100"], ["Febrero", "200"]]
        self.assertEqual(determine_chart_type(cols, rows), "line")

    def test_line_trimestre_keyword(self):
        cols = ["trimestre", "monto"]
        rows = [["Q1", "500"], ["Q2", "700"]]
        self.assertEqual(determine_chart_type(cols, rows), "line")

    def test_line_date_keyword(self):
        cols = ["date", "amount"]
        rows = [["2024-01-01", "100"], ["2024-02-01", "200"]]
        self.assertEqual(determine_chart_type(cols, rows), "line")

    # ── Boundary conditions ──────────────────────────────────────────────────

    def test_pie_exactly_8_rows(self):
        """Exactly 8 rows → pie (boundary: ≤ 8)"""
        cols = ["region", "total"]
        rows = [[str(i), str(i * 10)] for i in range(8)]
        self.assertEqual(determine_chart_type(cols, rows), "pie")

    def test_bar_exactly_9_rows(self):
        """Exactly 9 rows → bar (boundary: > 8)"""
        cols = ["region", "total"]
        rows = [[str(i), str(i * 10)] for i in range(9)]
        self.assertEqual(determine_chart_type(cols, rows), "bar")

    def test_table_all_none_second_col(self):
        """All None values in second column → no numeric sample → table"""
        cols = ["empresa", "monto"]
        rows = [["A", None], ["B", None]]
        self.assertEqual(determine_chart_type(cols, rows), "table")

    def test_numeric_actual_ints_in_rows(self):
        """Rows with actual int values (not strings) → must resolve correctly"""
        cols = ["region", "count"]
        rows = [{"region": "Norte", "count": 10},
                {"region": "Sur", "count": 20}]
        self.assertEqual(determine_chart_type(cols, rows), "pie")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestIsNumericValue))
    suite.addTests(loader.loadTestsFromTestCase(TestDetermineChartType))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
