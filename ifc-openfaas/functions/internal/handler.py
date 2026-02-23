def handle(event, context):
    body = event.body.decode() if event.body else ""
    return f"INTERNAL::{hash(body)}"
