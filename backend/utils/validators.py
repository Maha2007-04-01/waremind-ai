def validate_order_payload(data):
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"
    if "customer_name" not in data or not data["customer_name"]:
        return False, "customer_name is required"
    return True, None
