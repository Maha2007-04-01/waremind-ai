class InventoryItem:
    def __init__(self, id, product_id, location_id, quantity=0, reserved_quantity=0, damaged_quantity=0, available_quantity=None, last_updated=None):
        self.id = id
        self.product_id = product_id
        self.location_id = location_id
        self.quantity = quantity
        self.reserved_quantity = reserved_quantity
        self.damaged_quantity = damaged_quantity
        self.available_quantity = available_quantity if available_quantity is not None else max(0, quantity - reserved_quantity - damaged_quantity)
        self.last_updated = last_updated

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "location_id": self.location_id,
            "quantity": self.quantity,
            "reserved_quantity": self.reserved_quantity,
            "damaged_quantity": self.damaged_quantity,
            "available_quantity": self.available_quantity,
            "last_updated": self.last_updated
        }
