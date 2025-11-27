from opensearchpy import OpenSearch, exceptions as es_exceptions
from datetime import datetime
import asyncio
from app.config.config import ELASTICSEARCH_URL, ELASTICSEARCH_API_KEYU, ELASTICSEARCH_API_KEYP



# Conexión usando API Key
es = OpenSearch(
    ELASTICSEARCH_URL,  # Cambia por tu endpoint
    api_key=(ELASTICSEARCH_API_KEYU, ELASTICSEARCH_API_KEYP),
    headers={"Content-Type": "application/json"}
)

#guarda conversaciones
def index_conversation(user_id, message, message_type, classification, name, location, attachments, address_info):
    doc = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        "message_type": message_type,
        "classification": classification,
        "name": name,
        "location": location,
        "attachments": attachments,
        "addressInfo": {
            "display_name": address_info.get("display_name") if address_info else None,
            "address": {
                "town": address_info.get("address", {}).get("town") if address_info else None,
                "state": address_info.get("address", {}).get("state") if address_info else None,
                "county": address_info.get("address", {}).get("county") if address_info else None,
                "country": address_info.get("address", {}).get("country") if address_info else None,
                "postcode": address_info.get("address", {}).get("postcode") if address_info else None,
            } if address_info else {}
        }
    }
    print("Indexación en Elasticsearch:", doc)
    try:
        res = es.index(index="conversations", body=doc)
        print("Mensaje indexado con éxito", res['result'])
        return res
    except es_exceptions.ConnectionError as e:
        print("Error de conexión a Elasticsearch:", str(e))
    except Exception as e:
        print("Error al indexar el mensaje:", str(e))
    return None
 

#busqueda por user_id el historial
def search_conversations_by_user_id(user_id):
    # Tu código SÍNCRONO de Opensearch, usando request_timeout=5 por seguridad
    response = es.search(
        index="conversations",
        body={
            "query": {"match": {"user_id": user_id}},
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": 10
        },
        request_timeout=5
    )
    return response["hits"]["hits"]

async def call_search_with_timeout(user_id, timeout=5):
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, search_conversations_by_user_id, user_id),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        print("Timeout: búsqueda tardó más de 5 segundos.")
        return []


# busca 5 lugares aleatorios por subcategoria
def search_places_sync(sub_categoria: str):
    print(f"Ejecutando búsqueda síncrona de places para subcategoría: {sub_categoria}")
    """
    Busca 5 documentos aleatorios en el índice 'places' por SUB_CATEGORIA.
    """
    try:
        query_body = {
            "query": { 
                "function_score": { 
                    "query": {
                        "match": {
                            "SUB_CATEGORIA": sub_categoria 
                        }
                    },
                    "random_score": {},
                    "boost_mode": "replace"
                }
            }, 
            "sort": [{"_score": {"order": "desc"}}],
            "size": 5 
        }

        # Ejecución de la búsqueda con el timeout del cliente (Nivel 1)
        response = es.search(
            index="places",
            body=query_body,
            request_timeout=5  
        )
        return response.get("hits", {}).get("hits", [])
        
    except Exception as e:
        print(f"Error en la búsqueda síncrona de places: {e}")
        return []
    
async def get_random_places(sub_categoria: str, timeout: int = 5):
    """
    Llama a la búsqueda de lugares de forma asíncrona con un timeout estricto.
    
    :param sub_categoria: El valor exacto de la subcategoría (ej: 'GLAMPING').
    :param timeout: Tiempo máximo de espera para la operación completa.
    :return: Lista de 5 resultados aleatorios de Elasticsearch o lista vacía.
    """
    # Obtiene el event loop actual
    loop = asyncio.get_event_loop()
    
    print(f"Intentando buscar 5 lugares aleatorios de la subcategoría: {sub_categoria}")

    try:
        # Usa wait_for para forzar el timeout en el event loop
        result = await asyncio.wait_for(
            # Ejecuta la función síncrona en un thread pool (executor)
            loop.run_in_executor(None, search_places_sync, sub_categoria),
            timeout=timeout
        )
        # El resultado es la lista de hits de OpenSearch
        return result
        
    except asyncio.TimeoutError:
        print(f"❌ Timeout: La búsqueda de {sub_categoria} excedió el límite de {timeout} segundos.")
        return []
    except Exception as e:
        # Esto captura cualquier otro error inesperado
        print(f"❌ Error durante la ejecución asíncrona: {e}")
        return []
     
 
 # Busqueda por nombre exacto


#busca por nombre exacto
def search_place_by_name(name):
    # Tu código SÍNCRONO de Opensearch, usando request_timeout=5 por seguridad
    response = es.search(
        index="places",
        body={
            "query": {
            "bool": {
                # MUST: Búsqueda Fuzzy y de Patrones (Afecta el Score)
                "must": [
                    {
                        "multi_match": {
                            "query": name,
                            # Utiliza los subcampos generados por 'search_as_you_type'
                            "fields": [
                                "RAZON_SOCIAL_ESTABLECIMIENTO",
                                "RAZON_SOCIAL_ESTABLECIMIENTO._2gram",
                                "RAZON_SOCIAL_ESTABLECIMIENTO._3gram"
                            ],
                            "type": "bool_prefix",
                            "fuzziness": "AUTO" 
                        }
                    }
                ] 
                
            }
        },
        "size": 3, # Devolver un máximo de 3 resultados
        # Ordenar por el score de relevancia (el más parecido va primero)
        "sort": [{"_score": {"order": "desc"}}]
        },
        request_timeout=5
    )
    return response["hits"]["hits"]

async def search_place_by_name_with_timeout(name, timeout=5): 
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, search_place_by_name, name),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        print("Timeout: búsqueda tardó más de 5 segundos.")
        return []


# busca 5 lugares aleatorios por subcategoria
def search_places_byrnt(rnt: str):
    print(f"Ejecutando búsqueda síncrona de places para subcategoría: {rnt}")
    """
    Busca 5 documentos aleatorios en el índice 'places' por SUB_CATEGORIA.
    """
    try:
        query_body = {
            "query": {
                
                "function_score": {
              
                    "query": {
                        "match": {
                            "CODIGO_RNT": rnt 
                        }
                    },
                }
            },
             
            "sort": [{"_score": {"order": "desc"}}],
            "size": 1
        }

      
        response = es.search(
            index="places",
            body=query_body,
            request_timeout=5  
        )
        return response.get("hits", {}).get("hits", [])
        
    except Exception as e:
        print(f"Error en la búsqueda síncrona de places: {e}")
        return []
    
async def get_place_byrnt(rnt: str, timeout: int = 5):
    
    # Obtiene el event loop actual
    loop = asyncio.get_event_loop()
    
    print(f"Intentando buscar 5 lugares aleatorios de la subcategoría: {rnt}")

    try:
        # Usa wait_for para forzar el timeout en el event loop
        result = await asyncio.wait_for(
            # Ejecuta la función síncrona en un thread pool (executor)
            loop.run_in_executor(None, search_places_byrnt, rnt),
            timeout=timeout
        )
        # El resultado es la lista de hits de OpenSearch
        return result
        
    except asyncio.TimeoutError:
        print(f"❌ Timeout: La búsqueda de {rnt} excedió el límite de {timeout} segundos.")
        return []
    except Exception as e:
        # Esto captura cualquier otro error inesperado
        print(f"❌ Error durante la ejecución asíncrona: {e}")
        return []
     

# busca lugares cercanos, query geoespacial
def search_nearby_places_sync(latitud_usuario: float,   longitud_usuario: float,  radio_km: int = 5,  sub_categoria: str = None ):
   
    # 1. Definición del Filtro de Geolocalización (geo_distance)
    geo_filter = {
        "geo_distance": {
            "distance": f"{radio_km}km",
            "UBICACION": { # Asegúrate que este sea el campo geo_point en tu índice
                "lat": latitud_usuario,
                "lon": longitud_usuario
            }
        }
    }
    
    # 2. Construcción de la Consulta (Query Body)
    query_body = {
        "query": {
            "bool": {
                "filter": [
                    geo_filter # Aplicamos el filtro de distancia
                ]
            }
        },
        # 3. Ordenamiento por Distancia (Lo más cercano primero)
        "sort": [
            {
                "_geo_distance": {
                    "UBICACION": {
                        "lat": latitud_usuario,
                        "lon": longitud_usuario
                    },
                    "order": "asc", # Ascendente (del más cercano al más lejano)
                    "unit": "km"
                }
            }
        ],
         "sort": [{"_score": {"order": "desc"}}],
          "size": 3 # Limitar a 3 resultados
    }

    # 4. Añadir Filtro de Subcategoría (Opcional)
    if sub_categoria:
        print(f"-> Añadiendo filtro por SUB_CATEGORIA: {sub_categoria}")
        # Si se proporciona una subcategoría, la agregamos como un filtro 'must' dentro del 'bool'
        query_body["query"]["bool"]["filter"].append({
            "match": {
                "SUB_CATEGORIA": sub_categoria 
            }
        })

    try:
        # 5. Ejecución de la búsqueda
        response = es.search(
            index="places",
            body=query_body,
            request_timeout=5 
        )
        
        # 6. Extracción de resultados y adición de la distancia (opcional, pero útil)
        hits = response.get("hits", {}).get("hits", [])
        
        # Opcional: Procesar los hits para obtener la distancia real calculada por ES
        results = []
        for hit in hits:
            # La distancia calculada por ES se encuentra en el campo 'sort' del hit
            # El campo 'sort' contiene el valor del primer criterio de ordenación (la distancia)
            distance_km = hit["sort"][0] if hit.get("sort") else "N/A" 
            
            source = hit["_source"]
            source["DISTANCIA_KM"] = distance_km
            results.append(source)
            
        return results
        
    except Exception as e:
        print(f"Error en la búsqueda GEO de places: {e}")
        return []

async def get_place_near(latitud_usuario: float,   longitud_usuario: float,  radio_km: int = 5,  sub_categoria: str = None , timeout: int = 5):
    
    # Obtiene el event loop actual
    loop = asyncio.get_event_loop()
    print(f"Intentando buscar   lugares aleatorios de la  cercanos a la ubicación: {latitud_usuario}, {longitud_usuario} en un radio de {radio_km} km")
    try:
        # Usa wait_for para forzar el timeout en el event loop
        result = await asyncio.wait_for(
            # Ejecuta la función síncrona en un thread pool (executor)
            loop.run_in_executor(None, search_nearby_places_sync, latitud_usuario, longitud_usuario, radio_km, sub_categoria),
            timeout=timeout
        )
        # El resultado es la lista de hits de OpenSearch
        return result
        
    except asyncio.TimeoutError:
        print(f"❌ Timeout: La búsqueda  excedió el límite de {timeout} segundos.")
        return []
    except Exception as e:
        # Esto captura cualquier otro error inesperado
        print(f"❌ Error durante la ejecución asíncrona: {e}")
        return []
     
