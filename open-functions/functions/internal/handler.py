import json

def handle(event, context):
    try:
        data = json.loads(event.body.decode() if event.body else "{}")
        payload_to_process = data.get("payload", str(data))
    except Exception:
        payload_to_process = event.body.decode() if event.body else ""

    processed_data = f"INTERNAL::{hash(str(payload_to_process))}"

    envelope = {
        "ifc_metadata": {
            "classification": "internal"
        },
        "payload": processed_data
    }
    
    return json.dumps(envelope)