class Product:
    def __init__(self, id, sku, name, category="", description="", unit_price=0.0, 
                 reorder_level=10, safety_stock=5, weight=1.0, created_at=None):
        self.id = id
        self.sku = sku
        self.name = name
        self.category = category
        self.description = description
        self.unit_price = unit_price
        self.reorder_level = reorder_level
        self.safety_stock = safety_stock
        self.weight = weight
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "unit_price": self.unit_price,
            "reorder_level": self.reorder_level,
            "safety_stock": self.safety_stock,
            "weight": self.weight,
            "created_at": self.created_at
        }
