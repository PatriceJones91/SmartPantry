from fastapi import APIRouter, HTTPException
from pathlib import Path
import csv
import json
import urllib.request
import urllib.parse

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_CANDIDATES = [
    PROJECT_ROOT / "data" / "openfoodfacts_barcode_lookup.csv",
    PROJECT_ROOT / "openfoodfacts_barcode_lookup.csv",
    PROJECT_ROOT.parent / "backend" / "data" / "openfoodfacts_barcode_lookup.csv",
    PROJECT_ROOT.parent / "data" / "openfoodfacts_barcode_lookup.csv",
]


def clean(value):
    return str(value or "").strip()


def normalize_product(row, source="local_csv"):
    barcode = clean(row.get("barcode") or row.get("code") or row.get("upc"))
    name = clean(
        row.get("item_name")
        or row.get("product_name")
        or row.get("name")
        or row.get("food_name")
    )
    brand = clean(row.get("brand") or row.get("brands"))
    category = clean(row.get("category") or row.get("categories") or "Other")

    return {
        "barcode": barcode,
        "upc": barcode,
        "item_name": name,
        "name": name,
        "brand": brand,
        "category": category,
        "quantity": row.get("quantity") or 1,
        "unit": row.get("unit") or "item",
        "container_type": row.get("container_type") or "",
        "source": source,
        "found": True,
    }


def load_local_products():
    products = []

    for csv_path in CSV_CANDIDATES:
        if not csv_path.exists():
            continue

        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                product = normalize_product(row)
                if product["item_name"] or product["barcode"]:
                    products.append(product)

    return products


def lookup_local(query):
    query_clean = clean(query).lower()
    query_digits = "".join(ch for ch in query_clean if ch.isdigit())

    for product in load_local_products():
        product_barcode = clean(product.get("barcode")).lower()
        product_name = clean(product.get("item_name")).lower()
        product_brand = clean(product.get("brand")).lower()

        if query_digits and product_barcode.endswith(query_digits):
            return product

        if query_clean and query_clean in product_name:
            return product

        if query_clean and query_clean in product_brand:
            return product

    return None


def lookup_openfoodfacts(query):
    barcode = "".join(ch for ch in clean(query) if ch.isdigit())

    if len(barcode) < 8:
        return None

    url = f"https://world.openfoodfacts.org/api/v2/product/{urllib.parse.quote(barcode)}.json"

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "SmartPantry/1.0 capstone project"},
        )

        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != 1:
            return None

        product = data.get("product") or {}
        name = clean(product.get("product_name") or product.get("generic_name"))

        if not name:
            return None

        category = clean(product.get("categories_tags", ["Other"])[0] if product.get("categories_tags") else "Other")
        category = category.replace("en:", "").replace("-", " ").title()

        return {
            "barcode": barcode,
            "upc": barcode,
            "item_name": name,
            "name": name,
            "brand": clean(product.get("brands")),
            "category": category or "Other",
            "quantity": 1,
            "unit": "item",
            "container_type": "",
            "source": "openfoodfacts_api",
            "found": True,
        }

    except Exception:
        return None


def lookup_product(query):
    local_match = lookup_local(query)
    if local_match:
        return local_match

    api_match = lookup_openfoodfacts(query)
    if api_match:
        return api_match

    raise HTTPException(
        status_code=404,
        detail="No barcode or product match found. You can still enter the item manually.",
    )


@router.get("/barcodes/lookup/{query}")
def barcode_lookup(query: str):
    return lookup_product(query)


@router.get("/barcodes/{query}")
def barcode_lookup_short(query: str):
    return lookup_product(query)


@router.get("/barcode/lookup/{query}")
def barcode_lookup_alt(query: str):
    return lookup_product(query)
