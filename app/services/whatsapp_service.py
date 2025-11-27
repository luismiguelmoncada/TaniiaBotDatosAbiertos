from app.services.http_request.send_to_whatsapp import send_to_whatsapp, download_whatsapp_audio_async

class WhatsAppService:
    async def send_message(self, to, body, message_id=None):
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {"body": body},
        }
        if message_id:
            data["context"] = {"message_id": message_id}
        await send_to_whatsapp(data)

    async def send_interactive_buttons(self, to, body_text, buttons):
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": buttons
                }
            }
        }
        await send_to_whatsapp(data)

    async def send_media_message(self, to, media_type, media_url, caption=None):
        media_object = {}
        if media_type == "image":
            media_object["image"] = {"link": media_url, "caption": caption}
        elif media_type == "audio":
            media_object["audio"] = {"link": media_url}
        elif media_type == "video":
            media_object["video"] = {"link": media_url, "caption": caption}
        elif media_type == "document":
            media_object["document"] = {
                "link": media_url,
                "caption": caption,
                "filename": "tannia-file.pdf"
            }
        else:
            raise ValueError("Not Supported Media Type")
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": media_type,
            **media_object
        }
        await send_to_whatsapp(data)

    async def mark_as_read(self, message_id):
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        await send_to_whatsapp(data)

    async def send_contact_message(self, to, contact):
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "contacts",
            "contacts": [contact]
        }
        await send_to_whatsapp(data)

    async def send_location_message(self, to, latitude, longitude, name, address):
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address
            }
        }
        await send_to_whatsapp(data)

    async def load_whatsapp_audio(self,  message_id=None): 
       return await download_whatsapp_audio_async(media_id=message_id)

# Instancia global, como en JS
whatsapp_service = WhatsAppService()