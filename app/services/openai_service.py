from ast import arguments
import io
from urllib import response
import openai
from app.config.config import OPENAI_API_KEY
from app.services.elasticsearch_service import call_search_with_timeout
import json

# Crear el cliente asíncrono  API Key
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

async def openai_service(message: str,to:str, language: str,tool_calls=None) -> str:
    print("OpenAI Service Invoked")
    print("language:", language)

    #llamo a leastica para traer historia y concatenarlo al prompt
    response_elastic = await call_search_with_timeout(to, timeout=5)
    #print("Elastic Search Response:", response_elastic)
    historial_gpt = []
    for hit in response_elastic:
        src = hit.get('_source') or {}
        msg = src.get('message')
        classification = src.get('classification')
        respuesta_texto = ""
        if isinstance(classification, str):
            try:
                classification_dict = json.loads(classification)
                respuesta_texto = classification_dict.get("respuesta", "")
            except Exception as e:
                respuesta_texto = ""  # o maneja el error/log
        if isinstance(msg, str) and isinstance(classification, str):
            historial_gpt.append({
                "role": "user",
                "content": msg#[:100]
            })
            historial_gpt.append({
                "role": "assistant",
                "content": respuesta_texto#[:100]
            }) 
 
    output_language = language

    try: 
      
        #response = await client.chat.completions.create(
            #model="gpt-4o", #$2.5•$10
            #model="gpt-3.5-turbo", #0.5•$1.5
         #   model="gpt-4o-mini", #$0.15•$0.6
         #   messages=messages,
        #)
        #buscar_lugar_turistico, implementar
        tools_tannia = [
        
                    
                {
                    "type": "function",
                    "function": {
                        "name": "obtener_geolocalizacion",
                        "description": "Se utiliza exclusivamente cuando el usuario solicita la ubicación exacta, mapa, coordenadas o rutas para llegar a un lugar específico.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "nombre_lugar_mapa": {
                                    "type": "string",
                                    "description": "Nombre del lugar cuya geolocalización se solicita (ej: 'Basílica de Chiquinquirá' o 'El Morro')."
                                }
                            },
                            "required": ["nombre_lugar_mapa"]
                        }
                    }
                },
                
                {
                    "type": "function",
                    "function": {
                        "name": "cambiar_idioma_respuesta",
                        "description": "Se utiliza exclusivamente cuando el usuario solicita otro idioma (ej: 'Responde en inglés', 'Quiero hablar en francés', '¿Hablas ingles?').",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "idioma_solicitado": {
                                    "type": "string",
                                    "description": "El idioma al que el usuario desea cambiar la conversación (ej: 'inglés', 'francés', 'español')."
                                }
                            },
                            "required": ["idioma_solicitado"]
                        }
                    }
                    },
                {
                    "type": "function",
                    "function": {
                        "name": "manejar_conversacion_simple",
                        "description": "Se utiliza para responder a interacciones conversacionales que no son consultas de búsqueda turística o ubicación. Incluye saludos, despedidas, agradecimientos. Lo que no comprenda debe devolverlo como otra",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intencion_simple": {
                                    "type": "string",
                                    "enum": ["saludo", "agradecimiento", "despedida", "emergencia", "otra"],
                                    "description": "La intención conversacional detectada."
                                }
                            },
                            "required": ["intencion_simple"]
                        }
                    }
                }
        ]

        system_prompt = (
            "Eres Tannia, un agente de inteligencia artificial experta en turismo para Chiquinquira, Colombia. "
            "Hablas español, francés e inglés. *ORDEN PRIORITARIA:* No debes nunca inventar información. **INCLUSIÓN DE EMOJIS:** Utiliza emojis de forma estratégica para añadir tono y atractivo visual. Usa el historial de la conversación para mantener coherencia, personalización y contexto en el diálogo. " 
            )
        if tool_calls: 
            system_prompt +=f"**ORDEN PRIORITARIA:** El idioma de toda la respuesta DEBE ser en '{output_language}'. **Tu tarea es transformar el JSON** que recibiste en el role 'tool' en una **respuesta conversacional, amigable y útil** para el usuario. **ORDEN OBLIGATORIA:** Debes tambien transformar los datos de la lista de lugares que recibiste en el rol 'tool' en una respuesta conversacional. **DEBES LISTAR TODOS Y CADA UNO** de los nombres de los lugares proporcionados, sin excepción, usando un formato de lista numerada o con viñetas. NO generes frases genéricas. Tu respuesta debe empezar directamente con la lista de lugares."
        else:
            system_prompt +=f"**ORDEN PRIORITARIA:** El idioma de toda la respuesta DEBE ser en '{output_language}''. **Tu tarea es extraer la intension del usuario. **DEBES** devolver solo la funcion detectada." 

        print("SYSTEM PROMPT FINAL PARA GPT: ", system_prompt)
        # 2. Construimos la lista de mensajes completa
        mensajes_a_enviar = []
        mensajes_a_enviar.append({"role": "system", "content": system_prompt})# Primero el System Prompt

        
        if tool_calls:
            tool_calls_aux = tool_calls.copy()
            del tool_calls_aux["tool_call_id"]
            del tool_calls_aux["tool_call_message_original"]
            if "respuesta_preliminar" in tool_calls_aux:
                del tool_calls_aux["respuesta_preliminar"]
            if "result_bd" in tool_calls_aux:
                del tool_calls_aux["result_bd"]
 
            mensajes_a_enviar.extend([
            {
                "role": "user",
                "content": json.dumps(tool_calls.get("tool_call_message_original", ""), ensure_ascii=False), # Este debe ser el último mensaje que realmente detonó la tool call */
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id":  tool_calls.get("tool_call_id", ""),
                        "type": "function",  # <- ESTE CAMPO ES OBLIGATORIO
                        "function": {
                            "name": "clasificar_consulta_turismo",
                            "arguments": json.dumps(tool_calls_aux, ensure_ascii=False) #"{\"intencion\": \"CONSULTA_TURISMO\", \"entidades\": {\"nombre_lugar\": \"glamping\", \"tipo_entidad\": \"GLAMPING\", \"municipio\": \"Chiquinquirá\"}}"
                        }
                    }
                ]
            },
            {
                "role": "tool",
                "tool_call_id": tool_calls.get("tool_call_id", ""),
                "content":  json.dumps(tool_calls.get("result_bd", ""), ensure_ascii=False),  
            }
    ])
        else: 
            # Sumamos el historial acumulado, solo aca, cuando es tool_calls es porque ya respondio y no necesita historia, generaria mas ruido
            mensajes_a_enviar.extend(historial_gpt)

            # Agregamos el mensaje actual del usuario si no es tool call
            mensajes_a_enviar.append(
                {"role": "user", "content": f"El usuario dice: {message}"}
            )
       
        print("MESSAGES to GPT (FINALLLLL):    ", mensajes_a_enviar)
    
        openai_kwargs = {
            "model": "gpt-4o-mini",
            "messages": mensajes_a_enviar
        }

        if not tool_calls:
            openai_kwargs["tools"] = tools_tannia
            openai_kwargs["tool_choice"] = "auto" 
           
        response = await client.chat.completions.create(**openai_kwargs)

        print("Assistant response GPT:", response)

        response_message = response.choices[0].message

        if response_message.tool_calls:
             # 3. Procesar la respuesta (Ya viene estructurada)
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)


            if tool_call.id:
                arguments["tool_call_id"] = tool_call.id
                arguments["function_name"] = tool_call.function.name
                arguments["tool_call_message_original"] = message
                print("tool_call.id:", tool_call.id)

            print("Tool Call (RESPUESTA GPT):", tool_call) 
         
            print("arguments:", arguments)

            
        
            #return response.choices[0].message.content
            return json.dumps(arguments, ensure_ascii=False)
        else:
            return response_message.content
        
    except Exception as error:
        print("OpenAI Error:", error)
        return None
    
async def transcribe_audio(audio_content_bytes: bytes) -> str | None:
       
        if not audio_content_bytes:
            print("Error: No se proporcionó contenido de audio para transcribir.")
            return None
            
        try:
            print("Transcribiendo contenido de audio a texto con OpenAI Whisper...")
             
            audio_file_like_object = io.BytesIO(audio_content_bytes) 
            audio_file_like_object.name = "audio.ogg" 

            transcript = await client.audio.transcriptions.create(
                model="whisper-1", # Este es el modelo Whisper de OpenAI
                file=audio_file_like_object,
                response_format="text", # Para obtener solo el texto de la transcripción
                language="es" # Opcional: especificar el idioma para mejorar la precisión
            )
            print("Transcripción completada.",transcript)
            return transcript
            
        except openai.APIError as e:
            print(f"Error de la API de OpenAI al transcribir el audio: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al transcribir el audio: {e}")
            return None