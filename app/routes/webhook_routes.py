from fastapi import APIRouter, Request, Response
from app.controllers.webhook_controller import handle_incoming, verify_webhook

router = APIRouter()

@router.post("/webhook")
async def webhook_post(request: Request):
    return await handle_incoming(request)

@router.get("/webhook")
async def webhook_get(request: Request):
    return await verify_webhook(request)