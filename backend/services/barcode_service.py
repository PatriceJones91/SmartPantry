import csv
from pathlib import Path
from typing import Dict, List, Optional

BARCODE_PATH = Path(__file__).resolve().parent.parent / "data" / "barcode_lookup.csv"


def normalize_key(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "_")


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def get_first(row: Dict, possible_names: List[str], default: str = ""):
    normalized = {normalize_key(k): v for k, v in row.items()}

    for name in possible_names:
        key = normalize_key(name)
        if key in normalized and clean(normalized[key]):
            return clean(normalized[key])

    return default


def load_barcode_rows() -> List[Dict]:
    if not BARCODE_PATH.exists():
        return []

    with BARCODE_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def lookup_barcode(barcode: str) -> Optional[Dict]:
    barcode = clean(barcode)

    if not barcode:
        return None

    rows = load_barcode_rows()

    for row in rows:
        row_barcode = get_first(row, ["barcode", "upc", "code", "product_code"])

        if row_barcode == barcode:
            return {
                "barcode": row_barcode,
                "item_name": get_first(
                    row,
                    ["item_name", "name", "food_name", "product_name", "clean_name"],
                    "Unknown Item",
                ),
                "category": get_first(row, ["category", "food_category"], "Other"),
                "quantity": get_first(row, ["quantity", "amount", "servings"], "1"),
                "unit": get_first(row, ["unit", "serving_unit"], "item"),
                "container_type": get_first(row, ["container_type", "container", "package_type"], ""),
                "brand": get_first(row, ["brand", "brands"], ""),
                "source": get_first(row, ["source"], "barcode_lookup.csv"),
            }

    return None


def search_items(query: str, limit: int = 20) -> List[Dict]:
    query = clean(query).lower()

    if not query:
        return []

    rows = load_barcode_rows()
    results = []

    for row in rows:
        item_name = get_first(
            row,
            ["item_name", "name", "food_name", "product_name", "clean_name"],
            "",
        )

        barcode = get_first(row, ["barcode", "upc", "code", "product_code"], "")

        if query in item_name.lower() or query in barcode.lower():
            results.append(
                {
                    "barcode": barcode,
                    "item_name": item_name,
                    "category": get_first(row, ["category", "food_category"], "Other"),
                    "quantity": get_first(row, ["quantity", "amount", "servings"], "1"),
                    "unit": get_first(row, ["unit", "serving_unit"], "item"),
                    "container_type": get_first(row, ["container_type", "container", "package_type"], ""),
                    "brand": get_first(row, ["brand", "brands"], ""),
                    "source": get_first(row, ["source"], "barcode_lookup.csv"),
                }
            )

        if len(results) >= limit:
            break

    return results
