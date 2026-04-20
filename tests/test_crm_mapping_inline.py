"""
Inline validation tests for DOB-117 CRM field mapping.
Run standalone: python tests/test_crm_mapping_inline.py
"""
import json
import sys
import os

# Ensure project root is importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

MAPPING_PATH = os.path.join(ROOT, "context", "crm_field_mapping.json")

# ── Reproduce apply_field_mapping logic ──────────────────────────────────────

_CRM_MAPPING = None

def _get_crm_mapping() -> dict:
    global _CRM_MAPPING
    if _CRM_MAPPING is None:
        with open(MAPPING_PATH, encoding="utf-8") as f:
            _CRM_MAPPING = json.load(f)
    return _CRM_MAPPING


def apply_field_mapping(crm_object: dict, destination: str):
    mapping = _get_crm_mapping()
    destinations = mapping.get("destinations", {})
    if destination not in destinations:
        return None
    dest_config = destinations[destination]
    object_type = dest_config.get("object_type", "company")
    field_map = dest_config.get("field_map", {})
    excluded_fields = dest_config.get("excluded_fields", [])
    properties = {}
    for canonical_field, field_def in field_map.items():
        if canonical_field in excluded_fields:
            continue
        value = crm_object.get(canonical_field)
        if value is None:
            continue
        transform = field_def.get("transform")
        if transform == "join_semicolon":
            if isinstance(value, list):
                value = "; ".join(str(v) for v in value)
            else:
                value = str(value)
        property_name = field_def["property"]
        properties[property_name] = value
    return {
        "destination": destination,
        "object_type": object_type,
        "properties": properties,
    }


# ── Test data ────────────────────────────────────────────────────────────────

mock_crm = {
    "crm_id": "test-sa",
    "nombre": "Test S.A.",
    "total_adjudicado": 5000000.0,
    "num_proyectos": 3,
    "primer_proyecto": 2018,
    "ultimo_proyecto": 2023,
    "regiones": ["Metropolitana", "Valparaíso"],
    "sectores": ["Alimentos"],
    "tendencias": ["Digitalización"],
    "sostenible": True,
    "economia_circular": False,
    "en_leads": True,
    "lead_status": "Contactado",
    "proyectos": []
}

# ── Tests ────────────────────────────────────────────────────────────────────

results = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, name, detail))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


print("\n--- Test 1: JSON file is valid and has required structure ---")
try:
    raw = _get_crm_mapping()
    check("JSON parseable", True)
    check("Has 'destinations' key", "destinations" in raw)
    dests = raw.get("destinations", {})
    check("Has 'hubspot' destination", "hubspot" in dests)
    check("Has 'generic' destination", "generic" in dests)
    for dest_name in ("hubspot", "generic"):
        d = dests.get(dest_name, {})
        check(f"'{dest_name}' has 'field_map'", "field_map" in d, dest_name)
        check(f"'{dest_name}' has 'excluded_fields'", "excluded_fields" in d, dest_name)
except Exception as e:
    check("JSON parseable", False, str(e))


print("\n--- Test 2: apply_field_mapping with 'hubspot' ---")
result_hs = apply_field_mapping(mock_crm, "hubspot")
check("Returns a dict", isinstance(result_hs, dict))
check("destination == 'hubspot'", result_hs.get("destination") == "hubspot",
      f"got: {result_hs.get('destination')}")
check("'properties' key present", "properties" in result_hs)
props = result_hs.get("properties", {})
check("properties['name'] == 'Test S.A.'", props.get("name") == "Test S.A.",
      f"got: {props.get('name')}")
check(
    "properties['corfo_regiones'] == 'Metropolitana; Valparaíso'",
    props.get("corfo_regiones") == "Metropolitana; Valparaíso",
    f"got: {props.get('corfo_regiones')}"
)
check("crm_id excluded (not in properties)", "crm_id" not in props)
check("proyectos excluded (not in properties)", "proyectos" not in props)
check("corfo_num_proyectos == 3", props.get("corfo_num_proyectos") == 3,
      f"got: {props.get('corfo_num_proyectos')}")
check("corfo_monto_total == 5000000.0", props.get("corfo_monto_total") == 5000000.0,
      f"got: {props.get('corfo_monto_total')}")

print("\n--- Test 3: apply_field_mapping with 'generic' ---")
result_gen = apply_field_mapping(mock_crm, "generic")
check("Returns a dict", isinstance(result_gen, dict))
check("destination == 'generic'", result_gen.get("destination") == "generic")
gen_props = result_gen.get("properties", {})
check("properties['company_name'] == 'Test S.A.'", gen_props.get("company_name") == "Test S.A.",
      f"got: {gen_props.get('company_name')}")
check(
    "properties['regions'] == 'Metropolitana; Valparaíso'",
    gen_props.get("regions") == "Metropolitana; Valparaíso",
    f"got: {gen_props.get('regions')}"
)

print("\n--- Test 4: apply_field_mapping with unknown destination ---")
result_unk = apply_field_mapping(mock_crm, "unknown")
check("Returns None for unknown destination", result_unk is None,
      f"got: {result_unk}")

print("\n--- Test 5: join_semicolon with non-list value ---")
mock_non_list = dict(mock_crm)
mock_non_list["regiones"] = "Metropolitana"
result_nl = apply_field_mapping(mock_non_list, "hubspot")
check(
    "join_semicolon on string value returns string unchanged",
    result_nl["properties"].get("corfo_regiones") == "Metropolitana",
    f"got: {result_nl['properties'].get('corfo_regiones')}"
)

print("\n--- Test 6: None field value is skipped ---")
mock_none = dict(mock_crm)
mock_none["lead_status"] = None
result_none = apply_field_mapping(mock_none, "hubspot")
check("None value field is excluded from properties",
      "corfo_lead_status" not in result_none["properties"])

# ── Summary ──────────────────────────────────────────────────────────────────

passed = sum(1 for s, _, _ in results if s == "PASS")
failed = sum(1 for s, _, _ in results if s == "FAIL")
print(f"\n=== SUMMARY: {passed} passed / {failed} failed ===")
if failed:
    print("FAILURES:")
    for s, name, detail in results:
        if s == "FAIL":
            print(f"  - {name}: {detail}")
    sys.exit(1)
else:
    sys.exit(0)
