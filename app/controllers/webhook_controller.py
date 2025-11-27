import os
from fastapi import Request, Response
from app.config.config import WEBHOOK_VERIFY_TOKEN
from app.services.message_handler import message_handler  # Importa la instancia

async def handle_incoming(request: Request) -> Response:

    # Estas lineas podrian ser menos, pero al ser un webhook,  valida que venga todo bien lm20251106
    body = await request.json()
    entry = body.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    message = value.get("messages", [{}])
    message = message[0] if message else None
    sender_info = value.get("contacts", [{}])
    sender_info = sender_info[0] if sender_info else None

    print("Received message:", message)

    if message:
        await message_handler.handle_incoming_message(message, sender_info)

    return Response(status_code=200)

async def verify_webhook(request: Request) -> Response:
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(content=challenge, status_code=200)
    else:
        return Response(status_code=403)