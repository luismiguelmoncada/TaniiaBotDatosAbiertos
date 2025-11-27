import uvicorn
import os

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
         ssl_keyfile=os.environ.get("SSL_KEYFILE", "/app/privkey.pem"), # en /app de docker estan los archivos de ssl para correr en produccion con ssl lm20251106
         ssl_certfile=os.environ.get("SSL_CERTFILE", "/app/fullchain.pem")
    )

# Note: para corre locla en docker se crea la imagen y se corre asi docker run -p 3000:3000 bot-taniia
# no olvidar comentar y descomentar las lineas de ssl si se quiere correr con ssl o sin ssl