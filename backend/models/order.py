class Order:
    def __init__(self, id, order_number, customer_name, priority="NORMAL", status="PENDING", 
                 required_by=None, created_at=None, total_value=0.0, items=None):
        self.id = id
        self.order_number = order_number
        self.customer_name = customer_name
        self.priority = priority
        self.status = status
        self.required_by = required_by
        self.created_at = created_at
        self.total_value = total_value
        self.items = items or []

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_name": self.customer_name,
            "priority": self.priority,
            "status": self.status,
            "required_by": self.required_by,
            "created_at": self.created_at,
            "total_value": self.total_value,
            "items": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items]
        }

class OrderItem:
    def __init__(self, id, order_id, product_id, requested_quantity, allocated_quantity=0, picked_quantity=0, packed_quantity=0):
        self.id = id
        self.order_id = order_id
        self.product_id = product_id
        self.requested_quantity = requested_quantity
        self.allocated_quantity = allocated_quantity
        self.picked_quantity = picked_quantity
        self.packed_quantity = packed_quantity

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "requested_quantity": self.requested_quantity,
            "allocated_quantity": self.allocated_quantity,
            "picked_quantity": self.picked_quantity,
            "packed_quantity": self.packed_quantity
        }
