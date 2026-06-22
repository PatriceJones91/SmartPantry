from fastapi import APIRouter, HTTPException, Query

from services.barcode_service import lookup_barcode, search_items

router = APIRouter()


@router.get("/{barcode}")
def get_barcode_item(barcode: str):
    item = lookup_barcode(barcode)

    if not item:
        raise HTTPException(status_code=404, detail="Barcode not found.")

    return item


@router.get("")
def search_barcode_items(q: str = Query(default="", min_length=1), limit: int = 20):
    return search_items(q, limit)
