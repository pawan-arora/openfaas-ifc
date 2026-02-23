def handle(event, context):
    body = event.body.decode() if event.body else ""
    return f"PUBLIC::{hash(body)}"
