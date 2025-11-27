import httpx
from app.config.config import BASE_URL, API_VERSION, BUSINESS_PHONE, API_TOKEN

async def send_to_whatsapp(data):
    url = f"{BASE_URL}/{API_VERSION}/{BUSINESS_PHONE}/messages"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    
async def download_whatsapp_audio_async(media_id: str) -> bytes | None:
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Obtener los metadatos del medio para conseguir la URL de descarga
            media_metadata_url = f"{BASE_URL}/{API_VERSION}/{media_id}" # Puedes usar BASE_URL y API_VERSION aquí también
            print(f"Obteniendo metadatos de: {media_metadata_url}")
            response = await client.get(media_metadata_url, headers=headers)
            response.raise_for_status() # Lanza una excepción para errores HTTP
            media_data = response.json()
            print(f"Metadatos recibidos: {media_data}")
            
            if 'url' not in media_data:
                print(f"Error: No se encontró la URL de descarga para el media ID {media_id}. Respuesta: {media_data}")
                return None
                
            download_url = media_data['url']
            
            # 2. Descargar el archivo binario del audio
            print(f"Descargando audio binario de: {download_url}")
            file_response = await client.get(download_url, headers=headers)
            file_response.raise_for_status() # Lanza excepción si el status code indica error

            print(f"Tamaño del audio descargado",file_response)
            print(f"Tamaño del audio descargado: {len(file_response.content)} bytes")
            
            print(f"Audio con ID {media_id} descargado exitosamente.")
            return file_response.content # Retorna el contenido binario del audio
            
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP al descargar o obtener metadatos del medio {media_id}: {e}")
            print(f"Respuesta del servidor: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Error de red al intentar descargar o obtener metadatos del medio {media_id}: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al procesar el medio {media_id}: {e}")
            return None