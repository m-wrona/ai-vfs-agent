"""Products skill: catalog with pricing and inventory. Data loaded from workspace/products.md."""

import os


def _load_products():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "products.md")
    products = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.rstrip() for l in f if l.strip().startswith("|")]
    if len(lines) < 3:
        return products
    for row in lines[2:]:
        parts = [p.strip() for p in row.split("|") if p.strip()]
        if len(parts) >= 5:
            products.append({
                "id": parts[0],
                "name": parts[1],
                "price": float(parts[2]),
                "category": parts[3],
                "stock": int(parts[4]),
            })
    return products


products = _load_products()


def get_product_by_id(id):
    for p in products:
        if p["id"] == id:
            return p
    return None


def get_products_by_category(category):
    return [p for p in products if p["category"] == category]


def get_in_stock_products():
    return [p for p in products if p["stock"] > 0]
