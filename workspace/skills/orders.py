"""Orders skill: order data linked to products via productId. Data loaded from workspace/orders.md."""

import os

def _load_orders():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "orders.md")
    orders = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.rstrip() for l in f if l.strip().startswith("|")]
    if len(lines) < 3:
        return orders
    # lines[0] = header, lines[1] = separator, lines[2:] = rows
    for row in lines[2:]:
        parts = [p.strip() for p in row.split("|") if p.strip()]
        if len(parts) >= 6:
            orders.append({
                "id": parts[0],
                "productId": parts[1],
                "customerId": parts[2],
                "quantity": int(parts[3]),
                "date": parts[4],
                "status": parts[5],
            })
    return orders

orders = _load_orders()


def get_orders_by_product(product_id):
    return [o for o in orders if o["productId"] == product_id]


def get_orders_by_customer(customer_id):
    return [o for o in orders if o["customerId"] == customer_id]


def get_orders_by_status(status):
    return [o for o in orders if o["status"] == status]
