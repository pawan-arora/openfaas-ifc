import json

def handle(event, context):
    try:
        # Check if the input is a JSON envelope (from a pipeline)
        data = json.loads(event.body.decode() if event.body else "{}")
        # Extract the payload, or use the whole data if it wasn't an envelope
        payload_to_process = data.get("payload", str(data))
    except Exception:
        # Fallback for individual direct text requests
        payload_to_process = event.body.decode() if event.body else ""

    # Do the function's actual work
    processed_data = f"PUBLIC::{hash(str(payload_to_process))}"

    # Return the secure JSON envelope
    envelope = {
        "ifc_metadata": {
            "classification": "public"
        },
        "payload": processed_data
    }
    
    return json.dumps(envelope)