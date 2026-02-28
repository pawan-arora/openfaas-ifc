import json
import base64

def handle(event, context):
    raw_data = event.body.decode() if event.body else "No data"
    
    # 1. Simulate encrypting the sensitive data 
    encrypted_payload = base64.b64encode(raw_data.encode()).decode('utf-8')
    
    # 2. Build the secure envelope
    envelope = {
        "ifc_metadata": {
            "classification": "confidential",
            "encrypted": True
        },
        "payload": encrypted_payload
    }
    
    return json.dumps(envelope)