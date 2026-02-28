import json
import base64

def handle(event, context):
    try:
        # 1. Parse the incoming JSON envelope
        body = event.body.decode() if event.body else "{}"
        data = json.loads(body)
        
        metadata = data.get("ifc_metadata", {})
        
        # 2. Verify we are actually dealing with confidential data
        if metadata.get("classification") == "confidential":
            
            # 3. "Decrypt" the payload
            encrypted_payload = data.get("payload", "")
            try:
                decrypted_raw = base64.b64decode(encrypted_payload).decode('utf-8')
            except Exception:
                decrypted_raw = str(encrypted_payload) # Fallback if not strictly b64
            
            # 4. Apply the Declassification Rule (Redaction/Masking)
            # Example: Keep the first 4 characters, mask the rest
            redacted_payload = decrypted_raw[:4] + "****[REDACTED]"
            
            # 5. Lower the classification and update the audit trail
            data["payload"] = redacted_payload
            data["ifc_metadata"]["classification"] = "public"
            data["ifc_metadata"]["encrypted"] = False
            data["ifc_metadata"]["declassified_by"] = "ifc_declassifier_service"
            
            return json.dumps(data)
            
        return json.dumps({"error": "Data is not marked as confidential."})
        
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid secure envelope format."})
    except Exception as e:
        return json.dumps({"error": str(e)})