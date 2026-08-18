class WarehouseLocation:
    def __init__(self, id, zone, aisle, rack, bin, capacity=100, status="AVAILABLE"):
        self.id = id
        self.zone = zone
        self.aisle = aisle
        self.rack = rack
        self.bin = bin
        self.capacity = capacity
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "zone": self.zone,
            "aisle": self.aisle,
            "rack": self.rack,
            "bin": self.bin,
            "capacity": self.capacity,
            "status": self.status
        }
