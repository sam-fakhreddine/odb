import json


def handler(event, context):
    parameters = event.get("queryStringParameters") or {}
    try:
        quantity = int(parameters.get("quantity", ""))
        unit_cents = int(parameters.get("unit_cents", ""))
        discount = int(parameters.get("discount_percent", "0"))
    except (ValueError, TypeError):
        return {"statusCode": 400, "body": json.dumps({"error": "Use integer inputs"})}
    if not (1 <= quantity <= 100 and 1 <= unit_cents <= 1000000 and 0 <= discount <= 100):
        return {"statusCode": 400, "body": json.dumps({"error": "Inputs out of range"})}
    subtotal = quantity * unit_cents
    discount_cents = subtotal * discount // 100
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({
            "subtotal_cents": subtotal,
            "discount_cents": discount_cents,
            "total_cents": subtotal - discount_cents,
            "request_id": event["requestContext"]["requestId"],
        }),
    }
