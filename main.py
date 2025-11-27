from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routes.webhook_routes import router as webhook_router
import os

app = FastAPI()
app.include_router(webhook_router)

# Monta /static para servir archivos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=FileResponse)
async def home():
    index_path = os.path.join("app/static", "index.html")
    return FileResponse(index_path)

""" @app.get("/")
async def home():
    return "Nothing to see here.\nCheckout README.md to start." """